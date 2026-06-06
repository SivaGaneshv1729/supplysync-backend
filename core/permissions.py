from rest_framework.permissions import BasePermission
from apps.accounts.models import UserRole

class IsAdminUser(BasePermission):
    message = "Only administrators are allowed."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)

class IsWarehouseManagerOrAdmin(BasePermission):
    message = "Only warehouse managers or administrators are allowed."

    def has_permission(self, request, view):
        allowed_roles = [UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER]
        return bool(request.user and request.user.is_authenticated and request.user.role in allowed_roles)

class IsProcurementManagerOrAdmin(BasePermission):
    message = "Only procurement managers or administrators are allowed."

    def has_permission(self, request, view):
        allowed_roles = [UserRole.ADMIN, UserRole.PROCUREMENT_MANAGER]
        return bool(request.user and request.user.is_authenticated and request.user.role in allowed_roles)

class IsWarehouseManagerOrAdminOrStaff(BasePermission):
    message = "Only staff, warehouse managers, or administrators are allowed."

    def has_permission(self, request, view):
        allowed_roles = [UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER, UserRole.STAFF]
        return bool(request.user and request.user.is_authenticated and request.user.role in allowed_roles)

class IsOwnerOrAdmin(BasePermission):
    message = "You must be the owner of this object or an administrator to access it."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Check ownership dynamically
        if hasattr(obj, 'created_by_id'):
            return obj.created_by_id == request.user.id
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'performed_by_id'):
            return obj.performed_by_id == request.user.id
        if hasattr(obj, 'performed_by'):
            return obj.performed_by == request.user
        
        return False
