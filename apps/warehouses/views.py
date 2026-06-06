from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from core.exceptions import ResourceNotFoundException
from django_filters.rest_framework import DjangoFilterBackend
from .models import Warehouse
from .serializers import WarehouseSerializer, WarehouseDetailSerializer
from .filters import WarehouseFilter
from .services import create_warehouse, get_warehouse_with_summary, update_warehouse, delete_warehouse

class WarehouseListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request):
        warehouses = Warehouse.objects.filter(is_active=True).order_by('-created_at')
        
        # Filtering
        filterset = WarehouseFilter(request.GET, queryset=warehouses)
        if filterset.is_valid():
            warehouses = filterset.qs
            
        # Pagination
        paginator = self.settings.DEFAULT_PAGINATION_CLASS()
        page = paginator.paginate_queryset(warehouses, request, view=self)
        if page is not None:
            serializer = WarehouseSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WarehouseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = create_warehouse(serializer.validated_data)
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_201_CREATED)

class WarehouseDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        result = get_warehouse_with_summary(pk)
        if not result:
            raise ResourceNotFoundException()
        
        # The service returns a dict with 'warehouse' and 'summary'
        warehouse = result['warehouse']
        summary = result['summary']
        
        # Merge them for the serializer
        data = WarehouseSerializer(warehouse).data
        data.update(summary)
        return Response(data)

    def put(self, request, pk):
        serializer = WarehouseSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        warehouse = update_warehouse(pk, serializer.validated_data)
        if not warehouse:
            raise ResourceNotFoundException()
            
        return Response(WarehouseSerializer(warehouse).data)

    def delete(self, request, pk):
        success = delete_warehouse(pk)
        if not success:
            raise ResourceNotFoundException()
        return Response(status=status.HTTP_204_NO_CONTENT)
