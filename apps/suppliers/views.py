from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from core.exceptions import ResourceNotFoundException
from .serializers import SupplierSerializer
from .services import create_supplier, update_supplier, get_supplier_by_id, list_suppliers, delete_supplier

class SupplierListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request):
        filters = {
            'name': request.GET.get('name'),
            'city': request.GET.get('city'),
            'state': request.GET.get('state'),
        }
        
        # Determine page and page_size
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
            
        paginator = self.settings.DEFAULT_PAGINATION_CLASS()
        try:
            page_size = int(request.GET.get(paginator.page_size_query_param, paginator.page_size))
        except ValueError:
            page_size = paginator.page_size
            
        suppliers_slice = list_suppliers(filters, page, page_size)
        
        # We manually structure the paginated response since we are bypassing standard DRF paginator logic
        serializer = SupplierSerializer(suppliers_slice, many=True)
        return Response({
            'count': None, # Unknown total without a separate query
            'next': None,
            'previous': None,
            'results': serializer.data
        })

    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = create_supplier(serializer.validated_data)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)

class SupplierDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        supplier = get_supplier_by_id(pk)
        if not supplier:
            raise ResourceNotFoundException("Supplier not found.")
        return Response(SupplierSerializer(supplier).data)

    def put(self, request, pk):
        serializer = SupplierSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = update_supplier(pk, serializer.validated_data)
        return Response(SupplierSerializer(supplier).data)

    def delete(self, request, pk):
        delete_supplier(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
