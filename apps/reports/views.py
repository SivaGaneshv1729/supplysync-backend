from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser, IsWarehouseManagerOrAdmin, IsProcurementManagerOrAdmin
from . import services

class DashboardReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Instructions 3.3: ADMIN, WAREHOUSE_MANAGER, PROCUREMENT_MANAGER
        if request.user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'PROCUREMENT_MANAGER']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only authorized roles can view reports.")
            
        data = services.get_dashboard_summary()
        return Response(data)

class InventoryValuationReportView(APIView):
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin]

    def get(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        data = services.get_inventory_valuation(warehouse_id)
        return Response(data)

class PurchaseOrderSummaryReportView(APIView):
    permission_classes = [IsAdminUser | IsProcurementManagerOrAdmin]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not start_date or not end_date:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("start_date and end_date are required.")
            
        supplier_id = request.query_params.get('supplier_id')
        status = request.query_params.get('status')
        
        data = services.get_purchase_order_summary(start_date, end_date, supplier_id, status)
        return Response(data)

class SalesOrderSummaryReportView(APIView):
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not start_date or not end_date:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("start_date and end_date are required.")
            
        warehouse_id = request.query_params.get('warehouse_id')
        status = request.query_params.get('status')
        
        data = services.get_sales_order_summary(start_date, end_date, warehouse_id, status)
        return Response(data)
