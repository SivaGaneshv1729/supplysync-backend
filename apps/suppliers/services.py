import random
import string
from django.core.cache import cache
from django.db.models import QuerySet
from core.constants import SUPPLIER_CACHE_TTL
from core.exceptions import DuplicateResourceException, ResourceNotFoundException
from .models import Supplier

def _generate_supplier_code():
    return f"SUP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def create_supplier(data: dict) -> Supplier:
    supplier_code = data.get('supplier_code')
    if not supplier_code:
        supplier_code = _generate_supplier_code()
        
    if Supplier.objects.filter(supplier_code=supplier_code).exists():
        raise DuplicateResourceException("Supplier code already exists.", code="DUPLICATE_SUPPLIER_CODE")
        
    data['supplier_code'] = supplier_code
    supplier = Supplier.objects.create(**data)
    return supplier

def update_supplier(supplier_id: int, data: dict) -> Supplier:
    supplier = Supplier.objects.filter(id=supplier_id).first()
    if not supplier:
        raise ResourceNotFoundException("Supplier not found.")
        
    for key, value in data.items():
        setattr(supplier, key, value)
    supplier.save()
    
    cache.delete(f'suppliers:detail:{supplier_id}')
    return supplier

def get_supplier_by_id(supplier_id: int) -> Supplier:
    cache_key = f'suppliers:detail:{supplier_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached
        
    supplier = Supplier.objects.filter(id=supplier_id).first()
    if not supplier:
        return None
        
    cache.set(cache_key, supplier, timeout=SUPPLIER_CACHE_TTL)
    return supplier

def list_suppliers(filters: dict, page: int, page_size: int) -> QuerySet:
    qs = Supplier.objects.all().order_by('-created_at')
    
    name = filters.get('name')
    if name:
        qs = qs.filter(name__icontains=name)
        
    city = filters.get('city')
    if city:
        qs = qs.filter(city__icontains=city)
        
    state = filters.get('state')
    if state:
        qs = qs.filter(state__icontains=state)
        
    start = (page - 1) * page_size
    end = start + page_size
    
    return qs[start:end]

def delete_supplier(supplier_id: int) -> None:
    supplier = Supplier.objects.filter(id=supplier_id).first()
    if not supplier:
        raise ResourceNotFoundException("Supplier not found.")
        
    supplier.is_deleted = True
    supplier.is_active = False
    supplier.save()
    
    cache.delete(f'suppliers:detail:{supplier_id}')
