from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser, IsWarehouseManagerOrAdmin
from core.exceptions import ResourceNotFoundException
from .serializers import ProductSerializer, ProductDetailSerializer
from .filters import ProductFilter
from .models import Product
from .services import create_product, get_product_with_inventory

class ProductListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsWarehouseManagerOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        products = Product.objects.all().order_by('-created_at')
        
        filterset = ProductFilter(request.GET, queryset=products)
        if filterset.is_valid():
            products = filterset.qs
            
        paginator = self.settings.DEFAULT_PAGINATION_CLASS()
        page = paginator.paginate_queryset(products, request, view=self)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = create_product(serializer.validated_data)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        product_data = get_product_with_inventory(pk)
        if not product_data:
            raise ResourceNotFoundException()
        return Response(product_data)
