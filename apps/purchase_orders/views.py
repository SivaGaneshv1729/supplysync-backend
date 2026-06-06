from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsProcurementManagerOrAdmin, IsWarehouseManagerOrAdmin
from .serializers import PurchaseOrderSerializer, PurchaseOrderCreateSerializer, POReceiveSerializer, POCancelSerializer
from .services import create_purchase_order, submit_purchase_order, approve_purchase_order, receive_purchase_order, cancel_purchase_order
from .models import PurchaseOrder

class PurchaseOrderListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsProcurementManagerOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        pos = PurchaseOrder.objects.all().order_by('-created_at')
        
        paginator = self.settings.DEFAULT_PAGINATION_CLASS()
        page = paginator.paginate_queryset(pos, request, view=self)
        if page is not None:
            serializer = PurchaseOrderSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        serializer = PurchaseOrderSerializer(pos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = create_purchase_order(serializer.validated_data, request.user.id)
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_201_CREATED)

class PurchaseOrderSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        po = submit_purchase_order(pk)
        return Response(PurchaseOrderSerializer(po).data)

class PurchaseOrderApproveView(APIView):
    permission_classes = [IsWarehouseManagerOrAdmin()]

    def post(self, request, pk):
        po = approve_purchase_order(pk, request.user.id)
        return Response(PurchaseOrderSerializer(po).data)

class PurchaseOrderReceiveView(APIView):
    permission_classes = [IsWarehouseManagerOrAdmin()] # Typically WAREHOUSE_MANAGER receives

    def post(self, request, pk):
        serializer = POReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = receive_purchase_order(pk, serializer.validated_data, request.user.id)
        return Response(PurchaseOrderSerializer(po).data)

class PurchaseOrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = POCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = cancel_purchase_order(pk, serializer.validated_data['reason'])
        return Response(PurchaseOrderSerializer(po).data)
