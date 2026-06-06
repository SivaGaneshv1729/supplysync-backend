from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem

class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = ['id', 'product_id', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'unit_price', 'total_price']

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = SalesOrder
        fields = ['id', 'order_number', 'customer_name', 'customer_email', 'customer_phone', 'shipping_address', 'warehouse_id', 'status', 'total_amount', 'dispatched_at', 'delivered_at', 'created_by_id', 'notes', 'items', 'created_at']
        read_only_fields = ['id', 'order_number', 'status', 'total_amount', 'dispatched_at', 'delivered_at', 'created_by_id', 'created_at']

class SOCreateItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

class SalesOrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(required=True, allow_blank=False)
    customer_email = serializers.EmailField(required=True, allow_blank=False)
    customer_phone = serializers.CharField(required=True, allow_blank=False)
    shipping_address = serializers.CharField(required=True, allow_blank=False)
    warehouse_id = serializers.IntegerField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = serializers.ListField(child=SOCreateItemSerializer(), required=True)

class SOCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)
