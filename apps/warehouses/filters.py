import django_filters
from .models import Warehouse

class WarehouseFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name='city', lookup_expr='icontains')
    state = django_filters.CharFilter(field_name='state', lookup_expr='icontains')

    class Meta:
        model = Warehouse
        fields = ['city', 'state']
