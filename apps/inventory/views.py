from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsWarehouseManagerOrAdminOrStaff
from core.pagination import StandardResultsPagination
from .serializers import InventoryAdjustSerializer, InventoryTransferSerializer, InventoryTransactionSerializer, InventorySerializer
from .services import adjust_inventory, transfer_inventory, get_low_stock_alerts
from .models import Inventory

class InventoryAdjustView(APIView):
    permission_classes = [IsWarehouseManagerOrAdminOrStaff]

    def post(self, request):
        serializer = InventoryAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        txn = adjust_inventory(serializer.validated_data, request.user.id)
        return Response(InventoryTransactionSerializer(txn).data, status=status.HTTP_201_CREATED)

class InventoryTransferView(APIView):
    permission_classes = [IsWarehouseManagerOrAdminOrStaff]

    def post(self, request):
        serializer = InventoryTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        txns = transfer_inventory(serializer.validated_data, request.user.id)
        return Response({
            "outbound": InventoryTransactionSerializer(txns["outbound"]).data,
            "inbound": InventoryTransactionSerializer(txns["inbound"]).data
        }, status=status.HTTP_201_CREATED)

class LowStockAlertView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alerts = get_low_stock_alerts()
        return Response(alerts)

class WarehouseInventoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, warehouse_id):
        inventory = Inventory.objects.filter(warehouse_id=warehouse_id).order_by('-last_updated_at')
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(inventory, request, view=self)
        if page is not None:
            serializer = InventorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = InventorySerializer(inventory, many=True)
        return Response(serializer.data)
