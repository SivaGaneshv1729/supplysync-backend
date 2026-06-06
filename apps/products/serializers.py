from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=True)
    
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'description', 'category_id', 'unit_price', 'unit_of_measure', 'reorder_level', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'sku': {'required': False},
            'name': {'required': True, 'allow_blank': False},
            'unit_price': {'required': True, 'min_value': 0},
            'reorder_level': {'required': False, 'min_value': 0},
        }

class ProductDetailSerializer(ProductSerializer):
    inventory_by_warehouse = serializers.ListField(child=serializers.DictField(), read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['inventory_by_warehouse']
