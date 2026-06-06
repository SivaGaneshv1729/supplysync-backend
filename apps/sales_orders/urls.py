from django.urls import path
from .views import SalesOrderListCreateView, SalesOrderDispatchView, SalesOrderDeliverView, SalesOrderCancelView

urlpatterns = [
    path('', SalesOrderListCreateView.as_view(), name='so-list-create'),
    path('<int:pk>/dispatch/', SalesOrderDispatchView.as_view(), name='so-dispatch'),
    path('<int:pk>/deliver/', SalesOrderDeliverView.as_view(), name='so-deliver'),
    path('<int:pk>/cancel/', SalesOrderCancelView.as_view(), name='so-cancel'),
]
