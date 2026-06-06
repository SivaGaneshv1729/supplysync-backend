import random
import string
from django.db import models
from django.db.models import Sum, Count
from django.core.cache import cache
from core.constants import WAREHOUSE_CACHE_TTL
from core.exceptions import InvalidOperationException, DuplicateResourceException
from .models import Warehouse
from apps.inventory.models import Inventory

def _generate_warehouse_code():
    return f"WH-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def create_warehouse(data: dict) -> Warehouse:
    warehouse_code = data.get('warehouse_code')
    if not warehouse_code:
        warehouse_code = _generate_warehouse_code()
    
    if Warehouse.objects.filter(warehouse_code=warehouse_code).exists():
        raise DuplicateResourceException(detail="Warehouse code already exists.", code="DUPLICATE_WAREHOUSE_CODE")
        
    data['warehouse_code'] = warehouse_code
    warehouse = Warehouse.objects.create(**data)
    
    # Invalidate list cache
    cache.delete('warehouses:list')
    
    return warehouse

def get_warehouse_with_summary(warehouse_id: int) -> dict:
    cache_key = f'warehouses:detail:{warehouse_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    warehouse = Warehouse.objects.filter(id=warehouse_id).first()
    if not warehouse:
        return None

    # Calculate summary
    inventory_qs = Inventory.objects.filter(warehouse=warehouse)
    total_distinct = inventory_qs.filter(quantity_available__gt=0).count() # Or all distinct products stored? Spec says "total distinct products stored".
    total_quantity = inventory_qs.aggregate(Sum('quantity_available'))['quantity_available__sum'] or 0

    result = {
        'warehouse': warehouse,
        'summary': {
            'total_distinct_products': total_distinct,
            'total_quantity_available': total_quantity
        }
    }
    
    cache.set(cache_key, result, timeout=WAREHOUSE_CACHE_TTL)
    return result

def update_warehouse(warehouse_id: int, data: dict) -> Warehouse:
    warehouse = Warehouse.objects.filter(id=warehouse_id).first()
    if not warehouse:
        return None
        
    if 'warehouse_code' in data and data['warehouse_code'] != warehouse.warehouse_code:
        raise InvalidOperationException(detail="Warehouse code cannot be changed.", code="WAREHOUSE_CODE_IMMUTABLE")
        
    for key, value in data.items():
        if key != 'warehouse_code':
            setattr(warehouse, key, value)
    
    warehouse.save()
    
    cache.delete(f'warehouses:detail:{warehouse_id}')
    cache.delete('warehouses:list')
    
    return warehouse

def delete_warehouse(warehouse_id: int) -> bool:
    warehouse = Warehouse.objects.filter(id=warehouse_id).first()
    if not warehouse:
        return False
        
    active_inventory = Inventory.objects.filter(warehouse=warehouse).filter(
        models.Q(quantity_available__gt=0) | models.Q(quantity_reserved__gt=0)
    ).exists()
    
    if active_inventory:
        raise InvalidOperationException(
            detail="Cannot delete warehouse with active inventory.", 
            code="WAREHOUSE_HAS_ACTIVE_INVENTORY"
        )
        
    warehouse.is_deleted = True
    warehouse.is_active = False
    warehouse.save()
    
    cache.delete(f'warehouses:detail:{warehouse_id}')
    cache.delete('warehouses:list')
    
    return True
