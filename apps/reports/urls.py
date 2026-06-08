from django.urls import path
from .views import (
    DashboardReportView, 
    InventoryValuationReportView,
    PurchaseOrderSummaryReportView,
    SalesOrderSummaryReportView
)

urlpatterns = [
    path('dashboard/', DashboardReportView.as_view(), name='dashboard-summary'),
    path('inventory-valuation/', InventoryValuationReportView.as_view(), name='inventory-valuation'),
    path('purchase-orders/summary/', PurchaseOrderSummaryReportView.as_view(), name='purchase-order-summary'),
    path('sales-orders/summary/', SalesOrderSummaryReportView.as_view(), name='sales-order-summary'),
]
