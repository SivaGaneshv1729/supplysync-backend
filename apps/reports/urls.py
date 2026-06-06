from django.urls import path
from .views import DashboardSummaryView, InventoryValuationView

urlpatterns = [
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('inventory-valuation/', InventoryValuationView.as_view(), name='inventory-valuation'),
]
