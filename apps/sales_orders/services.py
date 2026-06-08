from datetime import datetime
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from core.exceptions import InvalidOperationException, ResourceNotFoundException
from apps.accounts.models import User
from apps.warehouses.models import Warehouse
from apps.products.models import Product
from apps.inventory.models import Inventory, InventoryTransaction, TransactionType
from .models import SalesOrder, SalesOrderItem, SalesOrderStatus
from .tasks import process_sales_order_created_event, process_sales_order_cancelled_event

def _generate_so_number():
    date_str = timezone.now().strftime("%Y%m%d")
    key = f"so-sequence:{date_str}"
    
    # Atomic sequence generation
    if not cache.add(key, 0, timeout=86400):
        seq = cache.incr(key)
    else:
        seq = cache.incr(key)
        
    return f"SO-{date_str}-{str(seq).zfill(4)}"

def create_sales_order(data: dict, created_by_user_id: int) -> SalesOrder:
    warehouse_id = data['warehouse_id']
    items_data = data['items']
    
    warehouse = Warehouse.objects.filter(id=warehouse_id).first()
    if not warehouse:
        raise ResourceNotFoundException("Warehouse not found.")
        
    created_by = User.objects.get(id=created_by_user_id)
    
    # Aggregate quantities for duplicate line items
    aggregated_items = {}
    for item in items_data:
        pid = item['product_id']
        aggregated_items[pid] = aggregated_items.get(pid, 0) + item['quantity']
        
    product_ids = list(aggregated_items.keys())
    
    with transaction.atomic():
        # Lock inventory rows
        inventory_qs = list(Inventory.objects.select_for_update().filter(
            warehouse_id=warehouse_id, product_id__in=product_ids
        ))
        inventory_map = {inv.product_id: inv for inv in inventory_qs}
        
        short_items = []
        for pid, qty in aggregated_items.items():
            inv = inventory_map.get(pid)
            if not inv or inv.quantity_available < qty:
                short_items.append({
                    'product_id': pid,
                    'sku': Product.objects.get(id=pid).sku,
                    'requested_quantity': qty,
                    'available_quantity': inv.quantity_available if inv else 0
                })
                
        if short_items:
            from core.exceptions import InsufficientStockException
            raise InsufficientStockException(
                detail={"error": "Insufficient stock for order.", "short_items": short_items}
            )
            
        # Create order in CONFIRMED status as per 4.6
        so = SalesOrder.objects.create(
            order_number=_generate_so_number(),
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_phone=data['customer_phone'],
            shipping_address=data['shipping_address'],
            warehouse=warehouse,
            status=SalesOrderStatus.CONFIRMED,
            notes=data.get('notes'),
            created_by=created_by
        )
        
        total_amount = 0
        for pid, qty in aggregated_items.items():
            inv = inventory_map[pid]
            inv.quantity_available -= qty
            inv.quantity_reserved += qty
            inv.save()
            
            product = Product.objects.get(id=pid)
            unit_price = product.unit_price
            line_total = qty * unit_price
            
            SalesOrderItem.objects.create(
                sales_order=so,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                total_price=line_total
            )
            total_amount += line_total
            
            # Invalidate product cache
            cache.delete(f'products:detail:{pid}')
            
        so.total_amount = total_amount
        so.save()
        
    # Invalidate low stock cache
    cache.delete('inventory:low-stock')
        
    process_sales_order_created_event.delay(so.id, created_by_user_id)
    return so

def dispatch_sales_order(so_id: int, performed_by_user_id: int) -> SalesOrder:
    performed_by = User.objects.get(id=performed_by_user_id)
        
    with transaction.atomic():
        so = SalesOrder.objects.select_for_update().filter(id=so_id).first()
        if not so:
            raise ResourceNotFoundException("Sales Order not found.")
            
        if so.status not in [SalesOrderStatus.PENDING, SalesOrderStatus.CONFIRMED, SalesOrderStatus.PROCESSING]:
            raise InvalidOperationException(f"Cannot dispatch SO in status {so.status}.", code="INVALID_STATUS")
            
        items = list(so.items.all())
        product_ids = [item.product_id for item in items]
        
        inventory_qs = list(Inventory.objects.select_for_update().filter(
            warehouse_id=so.warehouse_id, product_id__in=product_ids
        ))
        inventory_map = {inv.product_id: inv for inv in inventory_qs}
        
        for item in items:
            inv = inventory_map[item.product_id]
            inv.quantity_reserved -= item.quantity
            inv.save()
            
            InventoryTransaction.objects.create(
                product_id=item.product_id,
                warehouse_id=so.warehouse_id,
                transaction_type=TransactionType.OUTBOUND,
                quantity=item.quantity,
                reference_id=f"DISPATCH-{so.order_number}",
                performed_by=performed_by,
                notes=f"Dispatched for SO {so.order_number}"
            )
            
        so.status = SalesOrderStatus.DISPATCHED
        so.dispatched_at = timezone.now()
        so.save()
        
    return so

def deliver_sales_order(so_id: int) -> SalesOrder:
    with transaction.atomic():
        so = SalesOrder.objects.select_for_update().filter(id=so_id).first()
        if not so:
            raise ResourceNotFoundException("Sales Order not found.")
            
        if so.status != SalesOrderStatus.DISPATCHED:
            raise InvalidOperationException(f"Cannot deliver SO in status {so.status}.", code="INVALID_STATUS")
            
        so.status = SalesOrderStatus.DELIVERED
        so.delivered_at = timezone.now()
        so.save()
    return so

def cancel_sales_order(so_id: int, reason: str) -> SalesOrder:
    with transaction.atomic():
        so = SalesOrder.objects.select_for_update().filter(id=so_id).first()
        if not so:
            raise ResourceNotFoundException("Sales Order not found.")
            
        if so.status not in [SalesOrderStatus.PENDING, SalesOrderStatus.CONFIRMED]:
            raise InvalidOperationException(f"Cannot cancel SO in status {so.status}.", code="INVALID_STATUS")
            
        items = list(so.items.all())
        product_ids = [item.product_id for item in items]
        
        inventory_qs = list(Inventory.objects.select_for_update().filter(
            warehouse_id=so.warehouse_id, product_id__in=product_ids
        ))
        inventory_map = {inv.product_id: inv for inv in inventory_qs}
        
        for item in items:
            inv = inventory_map[item.product_id]
            inv.quantity_available += item.quantity
            inv.quantity_reserved -= item.quantity
            inv.save()
            
            # Invalidate product cache
            cache.delete(f'products:detail:{item.product_id}')
            
        so.status = SalesOrderStatus.CANCELLED
        so.notes = (so.notes or '') + f"\nCancelled: {reason}"
        so.save()
        
    # Invalidate low stock cache
    cache.delete('inventory:low-stock')
        
    process_sales_order_cancelled_event.delay(so.id)
    return so
