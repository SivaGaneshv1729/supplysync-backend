from django.urls import path
from .views import InventoryAdjustView, InventoryTransferView, LowStockAlertView, WarehouseInventoryView

urlpatterns = [
    path('adjust/', InventoryAdjustView.as_view(), name='inventory-adjust'),
    path('transfer/', InventoryTransferView.as_view(), name='inventory-transfer'),
    path('low-stock/', LowStockAlertView.as_view(), name='low-stock'),
    path('warehouse/<int:warehouse_id>/', WarehouseInventoryView.as_view(), name='warehouse-inventory'),
]
