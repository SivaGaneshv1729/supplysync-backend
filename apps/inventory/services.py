import logging
import uuid
from django.db import transaction
from django.core.cache import cache
from core.constants import LOW_STOCK_ALERT_TTL
from core.exceptions import InsufficientInventoryException, ResourceNotFoundException
from .models import Inventory, InventoryTransaction, TransactionType
from apps.products.models import Product
from apps.warehouses.models import Warehouse
from apps.accounts.models import User
from .tasks import process_inventory_updated_event, process_inventory_transfer_event

logger = logging.getLogger(__name__)

def check_and_publish_low_stock_alert(product_id: int, warehouse_id: int) -> None:
    inventory = Inventory.objects.filter(product_id=product_id, warehouse_id=warehouse_id).select_related('product', 'warehouse').first()
    if not inventory:
        return
        
    if inventory.quantity_available <= inventory.product.reorder_level:
        logger.warning(
            f"LOW STOCK ALERT: Product {inventory.product.sku} in Warehouse {inventory.warehouse.warehouse_code} "
            f"has {inventory.quantity_available} units remaining (reorder level: {inventory.product.reorder_level})"
        )
        cache.delete('inventory:low-stock')

def adjust_inventory(data: dict, performed_by_user_id: int) -> InventoryTransaction:
    product_id = data['product_id']
    warehouse_id = data['warehouse_id']
    transaction_type = data['transaction_type']
    quantity = data['quantity']
    notes = data.get('notes', '')
    
    with transaction.atomic():
        product = Product.objects.filter(id=product_id).first()
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        performed_by = User.objects.filter(id=performed_by_user_id).first()
        
        if not product or not warehouse:
            raise ResourceNotFoundException("Product or Warehouse not found.")
            
        inventory, created = Inventory.objects.select_for_update().get_or_create(
            product=product,
            warehouse=warehouse,
            defaults={'quantity_available': 0, 'quantity_reserved': 0, 'quantity_damaged': 0}
        )
        
        if transaction_type in [TransactionType.OUTBOUND, TransactionType.DAMAGE_REPORT]:
            if inventory.quantity_available < quantity:
                raise InsufficientInventoryException(code="INSUFFICIENT_INVENTORY")
                
        if transaction_type == TransactionType.INBOUND:
            inventory.quantity_available += quantity
        elif transaction_type == TransactionType.OUTBOUND:
            inventory.quantity_available -= quantity
        elif transaction_type == TransactionType.DAMAGE_REPORT:
            inventory.quantity_available -= quantity
            inventory.quantity_damaged += quantity
        elif transaction_type == TransactionType.ADJUSTMENT:
            # Adjustment can be positive or negative
            if inventory.quantity_available + quantity < 0:
                raise InsufficientInventoryException(code="INSUFFICIENT_INVENTORY")
            inventory.quantity_available += quantity
            
        inventory.save()
        
        txn = InventoryTransaction.objects.create(
            product=product,
            warehouse=warehouse,
            transaction_type=transaction_type,
            quantity=quantity,
            performed_by=performed_by,
            notes=notes
        )
        
    process_inventory_updated_event.delay(product_id, warehouse_id, transaction_type, quantity)
    return txn

def transfer_inventory(data: dict, performed_by_user_id: int) -> dict:
    product_id = data['product_id']
    source_id = data['source_warehouse_id']
    dest_id = data['destination_warehouse_id']
    quantity = data['quantity']
    notes = data.get('notes', '')
    
    if source_id == dest_id:
        raise ValueError("Source and destination warehouse must be different.")
        
    with transaction.atomic():
        # lock in consistent order to prevent deadlocks
        w_ids = sorted([source_id, dest_id])
        Inventory.objects.select_for_update().filter(product_id=product_id, warehouse_id__in=w_ids)
        
        source_inv = Inventory.objects.filter(product_id=product_id, warehouse_id=source_id).first()
        if not source_inv or source_inv.quantity_available < quantity:
            raise InsufficientInventoryException(code="INSUFFICIENT_INVENTORY")
            
        dest_inv, _ = Inventory.objects.get_or_create(
            product_id=product_id, warehouse_id=dest_id,
            defaults={'quantity_available': 0, 'quantity_reserved': 0, 'quantity_damaged': 0}
        )
        
        source_inv.quantity_available -= quantity
        source_inv.save()
        
        dest_inv.quantity_available += quantity
        dest_inv.save()
        
        ref_id = f"TRANSFER-{uuid.uuid4().hex[:8]}"
        performed_by = User.objects.get(id=performed_by_user_id)
        
        outbound_txn = InventoryTransaction.objects.create(
            product_id=product_id, warehouse_id=source_id,
            transaction_type=TransactionType.OUTBOUND, quantity=quantity,
            reference_id=ref_id, performed_by=performed_by, notes=notes
        )
        inbound_txn = InventoryTransaction.objects.create(
            product_id=product_id, warehouse_id=dest_id,
            transaction_type=TransactionType.INBOUND, quantity=quantity,
            reference_id=ref_id, performed_by=performed_by, notes=notes
        )
        
    process_inventory_transfer_event.delay(product_id, source_id, dest_id, quantity)
    return {"outbound": outbound_txn, "inbound": inbound_txn}

def get_low_stock_alerts() -> list:
    cache_key = 'inventory:low-stock'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
        
    # We need products where quantity_available <= reorder_level
    # We can do this with F expressions
    from django.db.models import F
    
    low_stock = Inventory.objects.filter(
        quantity_available__lte=F('product__reorder_level')
    ).select_related('product', 'warehouse')
    
    results = []
    for inv in low_stock:
        deficit = inv.product.reorder_level - inv.quantity_available
        results.append({
            'product_id': inv.product.id,
            'sku': inv.product.sku,
            'product_name': inv.product.name,
            'warehouse_id': inv.warehouse.id,
            'warehouse_name': inv.warehouse.name,
            'quantity_available': inv.quantity_available,
            'reorder_level': inv.product.reorder_level,
            'deficit': deficit
        })
        
    cache.set(cache_key, results, timeout=LOW_STOCK_ALERT_TTL)
    return results
