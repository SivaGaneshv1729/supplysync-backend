from rest_framework import serializers
from .models import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product_id', 'quantity_ordered', 'quantity_received', 'unit_price', 'total_price']
        read_only_fields = ['id', 'quantity_received', 'total_price']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'po_number', 'supplier_id', 'warehouse_id', 'status', 'total_amount', 'expected_delivery_date', 'actual_delivery_date', 'created_by_id', 'approved_by_id', 'notes', 'items', 'created_at']
        read_only_fields = ['id', 'po_number', 'status', 'total_amount', 'actual_delivery_date', 'created_by_id', 'approved_by_id', 'created_at']

class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(required=True)
    warehouse_id = serializers.IntegerField(required=True)
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Items
    items = serializers.ListField(child=serializers.DictField(), required=False)

class POReceiveItemSerializer(serializers.Serializer):
    po_item_id = serializers.IntegerField(required=True)
    quantity_received = serializers.IntegerField(required=True, min_value=1)

class POReceiveSerializer(serializers.Serializer):
    items = serializers.ListField(child=POReceiveItemSerializer(), required=True)
    actual_delivery_date = serializers.DateField(required=True)

class POCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)
