from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser, IsWarehouseManagerOrAdminOrStaff, IsProcurementManagerOrAdmin
from django.db.models import Sum, F
from apps.accounts.models import User
from apps.warehouses.models import Warehouse
from apps.products.models import Product
from apps.inventory.models import Inventory
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderStatus
from apps.sales_orders.models import SalesOrder, SalesOrderStatus

class DashboardSummaryView(APIView):
    # STAFF, WAREHOUSE_MANAGER, PROCUREMENT_MANAGER, ADMIN
    permission_classes = [IsAuthenticated] # We will just use IsAuthenticated and handle custom permissions or leave it to role checking

    def get_permissions(self):
        # We need a custom logic or just check user role directly in view
        return super().get_permissions()

    def get(self, request):
        user = request.user
        if user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'PROCUREMENT_MANAGER', 'STAFF']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access dashboard.")
            
        total_users = User.objects.count()
        total_warehouses = Warehouse.objects.filter(is_active=True).count()
        total_active_products = Product.objects.filter(is_active=True).count()
        low_stock_count = Inventory.objects.filter(quantity_available__lte=F('product__reorder_level')).count()
        pending_pos = PurchaseOrder.objects.filter(status__in=[PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING_APPROVAL]).count()
        pending_sos = SalesOrder.objects.filter(status=SalesOrderStatus.PENDING).count()
        
        return Response({
            "total_users": total_users,
            "total_warehouses": total_warehouses,
            "total_active_products": total_active_products,
            "low_stock_items": low_stock_count,
            "pending_purchase_orders": pending_pos,
            "pending_sales_orders": pending_sos
        })

class InventoryValuationView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        valuation = Inventory.objects.aggregate(
            total_value=Sum(F('quantity_available') * F('product__unit_price'))
        )['total_value'] or 0
        
        return Response({
            "total_inventory_value": valuation
        })
