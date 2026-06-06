import random
import string
from django.core.cache import cache
from core.constants import CATEGORY_TREE_TTL
from core.exceptions import DuplicateResourceException
from .models import Category

def _generate_category_code():
    return f"CAT-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def create_category(data: dict) -> Category:
    category_code = data.get('category_code')
    if not category_code:
        category_code = _generate_category_code()
        
    if Category.objects.filter(category_code=category_code).exists():
        raise DuplicateResourceException(detail="Category code already exists.", code="DUPLICATE_CATEGORY_CODE")
        
    data['category_code'] = category_code
    
    # Handle parent_category_id from incoming dict
    parent_id = data.pop('parent_category_id', None)
    if parent_id:
        data['parent_category'] = Category.objects.get(id=parent_id)
        
    category = Category.objects.create(**data)
    
    # Invalidate tree cache
    cache.delete('categories:tree')
    
    return category

def get_category_tree() -> list:
    cache_key = 'categories:tree'
    cached = cache.get(cache_key)
    if cached:
        return cached
        
    categories = list(Category.objects.all())
    
    # Build tree
    category_map = {cat.id: cat for cat in categories}
    tree = []
    
    for cat in categories:
        cat.children_list = []
        
    for cat in categories:
        if cat.parent_category_id:
            parent = category_map.get(cat.parent_category_id)
            if parent:
                parent.children_list.append(cat)
        else:
            tree.append(cat)
            
    # Function to recursively serialize
    def serialize_node(node):
        return {
            'id': node.id,
            'category_code': node.category_code,
            'name': node.name,
            'description': node.description,
            'children': [serialize_node(child) for child in node.children_list]
        }
        
    result = [serialize_node(root) for root in tree]
    
    cache.set(cache_key, result, timeout=CATEGORY_TREE_TTL)
    return result
