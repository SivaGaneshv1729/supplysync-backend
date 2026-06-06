from datetime import datetime
from django.db import transaction
from django.core.cache import cache
import redis
from django.conf import settings
from core.exceptions import InvalidOperationException, ResourceNotFoundException
from apps.accounts.models import User
from apps.suppliers.models import Supplier
from apps.warehouses.models import Warehouse
from apps.products.models import Product
from apps.inventory.services import adjust_inventory
from apps.inventory.models import TransactionType
from .models import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from .tasks import process_purchase_order_received_event

# Create a direct redis client for sequence generation
# Assuming standard Redis location for simplicity, or we can use django-redis if configured
import redis
# A bit of a hack to get the raw redis client from django caches, but we can also just use cache.incr
# Wait, Django's cache.incr doesn't easily set TTL if key doesn't exist, it raises ValueError in LocMem but works in Redis.
# Let's write a robust fallback since we don't have direct access to redis-py connection easily without parsing LOCATION.

def _generate_po_number():
    date_str = datetime.now().strftime("%Y%m%d")
    key = f"po-sequence:{date_str}"
    
    # In testing we might be using LocMemCache which behaves differently.
    try:
        seq = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=86400)
        seq = 1
        
    return f"PO-{date_str}-{str(seq).zfill(4)}"

def create_purchase_order(data: dict, created_by_user_id: int) -> PurchaseOrder:
    supplier_id = data.get('supplier_id')
    warehouse_id = data.get('warehouse_id')
    items_data = data.get('items', [])
    
    created_by = User.objects.get(id=created_by_user_id)
    supplier = Supplier.objects.get(id=supplier_id)
    warehouse = Warehouse.objects.get(id=warehouse_id)
    
    with transaction.atomic():
        po = PurchaseOrder.objects.create(
            po_number=_generate_po_number(),
            supplier=supplier,
            warehouse=warehouse,
            status=PurchaseOrderStatus.DRAFT,
            expected_delivery_date=data.get('expected_delivery_date'),
            notes=data.get('notes'),
            created_by=created_by,
        )
        
        total_amount = 0
        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            qty = item['quantity']
            unit_price = product.unit_price # Use current product price
            line_total = qty * unit_price
            
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=product,
                quantity_ordered=qty,
                unit_price=unit_price,
                total_price=line_total
            )
            total_amount += line_total
            
        po.total_amount = total_amount
        po.save()
        
    return po

def submit_purchase_order(po_id: int) -> PurchaseOrder:
    po = PurchaseOrder.objects.filter(id=po_id).first()
    if not po:
        raise ResourceNotFoundException("Purchase Order not found.")
        
    if not po.items.exists():
        raise InvalidOperationException("Purchase Order has no items.", code="PO_HAS_NO_ITEMS")
        
    if po.status != PurchaseOrderStatus.DRAFT:
        raise InvalidOperationException(f"Cannot submit PO in status {po.status}.", code="INVALID_STATUS")
        
    po.status = PurchaseOrderStatus.PENDING_APPROVAL
    po.save()
    return po

def approve_purchase_order(po_id: int, approved_by_user_id: int) -> PurchaseOrder:
    po = PurchaseOrder.objects.filter(id=po_id).first()
    if not po:
        raise ResourceNotFoundException("Purchase Order not found.")
        
    if po.status != PurchaseOrderStatus.PENDING_APPROVAL:
        raise InvalidOperationException(f"Cannot approve PO in status {po.status}.", code="INVALID_STATUS")
        
    if po.created_by_id == approved_by_user_id:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(detail="Self approval not allowed.", code="SELF_APPROVAL_NOT_ALLOWED")
        
    po.status = PurchaseOrderStatus.APPROVED
    po.approved_by_id = approved_by_user_id
    po.save()
    return po

def receive_purchase_order(po_id: int, data: dict, performed_by_user_id: int) -> PurchaseOrder:
    po = PurchaseOrder.objects.filter(id=po_id).first()
    if not po:
        raise ResourceNotFoundException("Purchase Order not found.")
        
    if po.status not in [PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.PARTIALLY_RECEIVED]:
        raise InvalidOperationException(f"Cannot receive PO in status {po.status}.", code="INVALID_STATUS")
        
    items_to_receive = {item['po_item_id']: item['quantity_received'] for item in data['items']}
    
    with transaction.atomic():
        po_items = list(po.items.all())
        all_fully_received = True
        
        for item in po_items:
            if item.id in items_to_receive:
                recv_qty = items_to_receive[item.id]
                remaining = item.quantity_ordered - item.quantity_received
                if recv_qty > remaining:
                    raise InvalidOperationException(f"Cannot receive {recv_qty} for item {item.id}. Only {remaining} remaining.", code="EXCEEDS_ORDERED_QTY")
                    
                item.quantity_received += recv_qty
                item.save()
                
                # Adjust inventory
                adjust_inventory({
                    'product_id': item.product_id,
                    'warehouse_id': po.warehouse_id,
                    'transaction_type': TransactionType.INBOUND,
                    'quantity': recv_qty,
                    'notes': f"Received against PO {po.po_number}"
                }, performed_by_user_id)
                
            if item.quantity_received < item.quantity_ordered:
                all_fully_received = False
                
        po.actual_delivery_date = data['actual_delivery_date']
        if all_fully_received:
            po.status = PurchaseOrderStatus.RECEIVED
        else:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
        po.save()
        
    process_purchase_order_received_event.delay(po.id, performed_by_user_id)
    return po

def cancel_purchase_order(po_id: int, reason: str) -> PurchaseOrder:
    po = PurchaseOrder.objects.filter(id=po_id).first()
    if not po:
        raise ResourceNotFoundException("Purchase Order not found.")
        
    allowed_statuses = [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING_APPROVAL, PurchaseOrderStatus.APPROVED]
    if po.status not in allowed_statuses:
        raise InvalidOperationException(f"Cannot cancel PO in status {po.status}.", code="PO_CANCELLATION_NOT_ALLOWED")
        
    po.status = PurchaseOrderStatus.CANCELLED
    po.notes = (po.notes or '') + f"\nCancelled: {reason}"
    po.save()
    return po
