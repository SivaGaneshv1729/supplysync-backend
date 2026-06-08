import logging
from django.db.models import Sum, F, Count, Q, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from core.constants import DASHBOARD_CACHE_TTL
from apps.accounts.models import User
from apps.warehouses.models import Warehouse
from apps.products.models import Product
from apps.inventory.models import Inventory, InventoryTransaction, TransactionType
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderStatus
from apps.sales_orders.models import SalesOrder, SalesOrderStatus, SalesOrderItem

logger = logging.getLogger(__name__)

def get_dashboard_summary() -> dict:
    cache_key = 'reports:dashboard'
    cached = cache.get(cache_key)
    if cached:
        return cached

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Total inventory value
    total_inventory_value = Inventory.objects.filter(is_deleted=False).annotate(
        line_value=ExpressionWrapper(F('quantity_available') * F('product__unit_price'), output_field=DecimalField())
    ).aggregate(total=Sum('line_value'))['total'] or 0

    # Top selling products (last 30 days)
    top_selling = InventoryTransaction.objects.filter(
        transaction_type=TransactionType.OUTBOUND,
        created_at__gte=thirty_days_ago
    ).values('product_id', 'product__sku', 'product__name').annotate(
        total_dispatched=Sum('quantity')
    ).order_by('-total_dispatched')[:5]

    # Recent transactions
    recent_txns = InventoryTransaction.objects.select_related('product', 'warehouse', 'performed_by').order_by('-created_at')[:10]
    recent_txns_data = [{
        'id': t.id,
        'product_sku': t.product.sku,
        'warehouse_name': t.warehouse.name,
        'type': t.transaction_type,
        'quantity': t.quantity,
        'performed_by': t.performed_by.full_name,
        'created_at': t.created_at
    } for t in recent_txns]

    summary = {
        "total_warehouses": Warehouse.objects.filter(is_active=True).count(),
        "total_products": Product.objects.filter(is_active=True).count(),
        "total_suppliers": User.objects.count(), # This should be Supplier count, fixing:
        "total_inventory_value": str(total_inventory_value),
        "open_purchase_orders": PurchaseOrder.objects.filter(status__in=[PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING_APPROVAL, PurchaseOrderStatus.APPROVED]).count(),
        "pending_sales_orders": SalesOrder.objects.filter(status=SalesOrderStatus.PENDING).count(),
        "low_stock_product_count": Inventory.objects.filter(quantity_available__lte=F('product__reorder_level')).count(),
        "top_selling_products": list(top_selling),
        "recent_transactions": recent_txns_data
    }
    
    # Fix total_suppliers
    from apps.suppliers.models import Supplier
    summary["total_suppliers"] = Supplier.objects.filter(is_active=True).count()

    cache.set(cache_key, summary, timeout=DASHBOARD_CACHE_TTL)
    return summary

def get_inventory_valuation(warehouse_id: int = None) -> dict:
    warehouses = Warehouse.objects.filter(is_active=True)
    if warehouse_id:
        warehouses = warehouses.filter(id=warehouse_id)

    valuation_data = []
    grand_total = 0

    for wh in warehouses:
        items = Inventory.objects.filter(warehouse=wh, is_deleted=False).select_related('product')
        wh_total = 0
        wh_items = []
        
        for item in items:
            line_val = item.quantity_available * item.product.unit_price
            wh_items.append({
                'sku': item.product.sku,
                'product_name': item.product.name,
                'quantity_available': item.quantity_available,
                'unit_price': str(item.product.unit_price),
                'total_value': str(line_val)
            })
            wh_total += line_val
            
        valuation_data.append({
            'warehouse_id': wh.id,
            'warehouse_name': wh.name,
            'products': wh_items,
            'warehouse_total_value': str(wh_total)
        })
        grand_total += wh_total

    return {
        'grand_total_value': str(grand_total),
        'warehouses': valuation_data
    }

def get_purchase_order_summary(start_date, end_date, supplier_id=None, status=None) -> dict:
    qs = PurchaseOrder.objects.filter(created_at__date__range=[start_date, end_date])
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    if status:
        qs = qs.filter(status=status)

    metrics = qs.aggregate(
        total_orders=Count('id'),
        total_value=Sum('total_amount')
    )

    breakdown = qs.values('status').annotate(
        count=Count('id'),
        total_value=Sum('total_amount')
    )

    top_suppliers = qs.values('supplier_id', 'supplier__name').annotate(
        total_value=Sum('total_amount')
    ).order_by('-total_value')[:5]

    return {
        'total_orders': metrics['total_orders'] or 0,
        'total_value': str(metrics['total_value'] or 0),
        'breakdown_by_status': list(breakdown),
        'top_suppliers': list(top_suppliers)
    }

def get_sales_order_summary(start_date, end_date, warehouse_id=None, status=None) -> dict:
    qs = SalesOrder.objects.filter(created_at__date__range=[start_date, end_date])
    if warehouse_id:
        qs = qs.filter(warehouse_id=warehouse_id)
    if status:
        qs = qs.filter(status=status)

    delivered_qs = qs.filter(status=SalesOrderStatus.DELIVERED)
    delivered_metrics = delivered_qs.aggregate(
        total_revenue=Sum('total_amount'),
        count=Count('id')
    )
    
    total_rev = delivered_metrics['total_revenue'] or 0
    count_del = delivered_metrics['count'] or 0
    avg_val = total_rev / count_del if count_del > 0 else 0

    breakdown = qs.values('status').annotate(
        count=Count('id'),
        total_value=Sum('total_amount')
    )

    top_products = SalesOrderItem.objects.filter(
        sales_order__in=qs
    ).values('product_id', 'product__name').annotate(
        revenue=Sum('total_price')
    ).order_by('-revenue')[:5]

    return {
        'total_orders': qs.count(),
        'total_revenue': str(total_rev),
        'average_order_value': str(avg_val),
        'breakdown_by_status': list(breakdown),
        'top_products_by_revenue': list(top_products)
    }
