import random
import string
from django.core.cache import cache
from core.constants import PRODUCT_CACHE_TTL
from core.exceptions import DuplicateResourceException, ResourceNotFoundException
from .models import Product
from apps.categories.models import Category
from apps.inventory.models import Inventory

def _generate_product_sku(category_code: str) -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SKU-{category_code}-{random_str}"

def create_product(data: dict) -> Product:
    category_id = data.get('category_id')
    category = Category.objects.filter(id=category_id).first()
    if not category:
        raise ResourceNotFoundException(detail="Category not found.", code="CATEGORY_NOT_FOUND")
        
    sku = data.get('sku')
    if not sku:
        sku = _generate_product_sku(category.category_code)
        
    if Product.objects.filter(sku=sku).exists():
        raise DuplicateResourceException(detail="Product SKU already exists.", code="DUPLICATE_PRODUCT_SKU")
        
    data['sku'] = sku
    
    # We remove category_id to assign category directly, or let DRF handle it? 
    # Since we are in service, we handle it:
    data.pop('category_id', None)
    data['category'] = category
    
    product = Product.objects.create(**data)
    
    cache.delete('products:list')
    return product

def get_product_with_inventory(product_id: int) -> dict:
    cache_key = f'products:detail:{product_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    product = Product.objects.filter(id=product_id).first()
    if not product:
        return None

    inventory_records = Inventory.objects.filter(product=product).select_related('warehouse')
    inventory_by_warehouse = []
    
    for record in inventory_records:
        inventory_by_warehouse.append({
            'warehouse_id': record.warehouse.id,
            'warehouse_name': record.warehouse.name,
            'quantity_available': record.quantity_available,
            'quantity_reserved': record.quantity_reserved
        })
        
    # Serialize product data manually or return dict for DRF serializer
    from .serializers import ProductSerializer
    product_data = ProductSerializer(product).data
    product_data['inventory_by_warehouse'] = inventory_by_warehouse
    
    cache.set(cache_key, product_data, timeout=PRODUCT_CACHE_TTL)
    return product_data
