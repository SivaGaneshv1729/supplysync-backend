from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from .serializers import CategorySerializer
from .services import create_category, get_category_tree

class CategoryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request):
        categories = Category.objects.all().order_by('-created_at')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = create_category(serializer.validated_data)
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)

class CategoryTreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tree = get_category_tree()
        return Response(tree)
