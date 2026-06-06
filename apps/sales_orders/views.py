from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsWarehouseManagerOrAdmin, IsAdminUser
from .serializers import SalesOrderSerializer, SalesOrderCreateSerializer, SOCancelSerializer
from .services import create_sales_order, dispatch_sales_order, deliver_sales_order, cancel_sales_order
from .models import SalesOrder

class SalesOrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sos = SalesOrder.objects.all().order_by('-created_at')
        
        paginator = self.settings.DEFAULT_PAGINATION_CLASS()
        page = paginator.paginate_queryset(sos, request, view=self)
        if page is not None:
            serializer = SalesOrderSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        serializer = SalesOrderSerializer(sos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SalesOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        so = create_sales_order(serializer.validated_data, request.user.id)
        return Response(SalesOrderSerializer(so).data, status=status.HTTP_201_CREATED)

class SalesOrderDispatchView(APIView):
    permission_classes = [IsWarehouseManagerOrAdmin()]

    def post(self, request, pk):
        so = dispatch_sales_order(pk, request.user.id)
        return Response(SalesOrderSerializer(so).data)

class SalesOrderDeliverView(APIView):
    permission_classes = [IsAuthenticated] # usually drivers or anyone authorized

    def post(self, request, pk):
        so = deliver_sales_order(pk)
        return Response(SalesOrderSerializer(so).data)

class SalesOrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = SOCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        so = cancel_sales_order(pk, serializer.validated_data['reason'])
        return Response(SalesOrderSerializer(so).data)
