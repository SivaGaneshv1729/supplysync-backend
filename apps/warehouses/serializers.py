from rest_framework import serializers
from .models import Warehouse

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'warehouse_code', 'name', 'location', 'city', 'state', 'pincode', 'capacity', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'warehouse_code': {'required': False},
            'name': {'required': True, 'allow_blank': False},
            'location': {'required': True, 'allow_blank': False},
            'city': {'required': True, 'allow_blank': False},
            'state': {'required': True, 'allow_blank': False},
            'pincode': {'required': True, 'allow_blank': False},
            'capacity': {'required': True, 'min_value': 0},
        }

class WarehouseDetailSerializer(WarehouseSerializer):
    total_distinct_products = serializers.IntegerField(read_only=True)
    total_quantity_available = serializers.IntegerField(read_only=True)

    class Meta(WarehouseSerializer.Meta):
        fields = WarehouseSerializer.Meta.fields + ['total_distinct_products', 'total_quantity_available']
