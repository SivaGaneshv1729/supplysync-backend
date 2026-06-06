from rest_framework.exceptions import APIException, ValidationError, NotAuthenticated, PermissionDenied
from rest_framework.views import exception_handler
from django.utils import timezone

class ResourceNotFoundException(APIException):
    status_code = 404
    default_code = 'RESOURCE_NOT_FOUND'
    default_detail = 'Resource not found.'

class DuplicateResourceException(APIException):
    status_code = 409
    default_code = 'DUPLICATE_RESOURCE'
    default_detail = 'Duplicate resource.'

class InsufficientInventoryException(APIException):
    status_code = 422
    default_code = 'INSUFFICIENT_INVENTORY'
    default_detail = 'Insufficient inventory.'

class InsufficientStockException(APIException):
    status_code = 422
    default_code = 'INSUFFICIENT_STOCK_FOR_ORDER'
    default_detail = 'Insufficient stock for order.'

class InvalidOperationException(APIException):
    status_code = 422
    default_code = 'INVALID_OPERATION'
    default_detail = 'Invalid operation.'

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    
    # If unhandled, this could be a standard Exception
    if response is None:
        status_code = 500
        error_code = 'INTERNAL_SERVER_ERROR'
        message = str(exc)
        errors = []
    else:
        status_code = response.status_code
        if isinstance(exc, ValidationError):
            error_code = 'VALIDATION_FAILED'
            message = 'Validation failed.'
            # DRF ValidationError details can be dict or list
            errors = []
            if isinstance(response.data, dict):
                for field, field_errors in response.data.items():
                    if isinstance(field_errors, list):
                        for err in field_errors:
                            errors.append({"field": field, "message": str(err)})
                    else:
                        errors.append({"field": field, "message": str(field_errors)})
            elif isinstance(response.data, list):
                for err in response.data:
                    errors.append({"field": "non_field_errors", "message": str(err)})
        else:
            errors = []
            if isinstance(exc, NotAuthenticated):
                error_code = 'NOT_AUTHENTICATED'
            elif isinstance(exc, PermissionDenied):
                error_code = 'PERMISSION_DENIED'
            elif hasattr(exc, 'default_code'):
                error_code = exc.default_code
            else:
                error_code = 'ERROR'
            
            # The message is usually in response.data['detail'] or we fallback to string exc
            if isinstance(response.data, dict) and 'detail' in response.data:
                message = str(response.data['detail'])
            else:
                message = str(exc)

    request = context.get('request')
    path = request.path if request else ''

    unified_response = {
        "timestamp": timezone.now().isoformat(),
        "status": status_code,
        "error_code": error_code,
        "message": message,
        "path": path,
        "errors": errors
    }

    if response is not None:
        response.data = unified_response
    else:
        from rest_framework.response import Response
        response = Response(unified_response, status=status_code)
        
    return response
