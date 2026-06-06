from rest_framework import serializers
from .models import Inventory, InventoryTransaction, TransactionType

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'product_id', 'warehouse_id', 'quantity_available', 'quantity_reserved', 'quantity_damaged', 'last_updated_at']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = '__all__'

class InventoryAdjustSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    warehouse_id = serializers.IntegerField(required=True)
    transaction_type = serializers.ChoiceField(choices=TransactionType.choices, required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class InventoryTransferSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    source_warehouse_id = serializers.IntegerField(required=True)
    destination_warehouse_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
