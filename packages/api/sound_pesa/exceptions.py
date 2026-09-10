"""
Custom exception handlers for the Sound Pesa API.
"""
import logging
import uuid
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error for business logic validation."""
    pass


class BlockchainError(Exception):
    """Custom error for blockchain-related operations."""
    pass


class InsufficientBalanceError(ValidationError):
    """Error raised when wallet has insufficient balance."""
    pass


class TransactionError(Exception):
    """Base error for transaction-related operations."""
    pass

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())
    
    if response is not None:
        # Log the error with context
        logger.error(
            f"API Error - Request ID: {request_id}, "
            f"Status: {response.status_code}, "
            f"Exception: {exc.__class__.__name__}, "
            f"Message: {str(exc)}"
        )
        
        # Customize the error response format
        custom_response_data = {
            'error': {
                'code': get_error_code(exc, response.status_code),
                'message': get_error_message(exc, response.data),
                'details': response.data if isinstance(response.data, dict) else {},
                'timestamp': context['request'].META.get('HTTP_X_TIMESTAMP'),
                'request_id': request_id
            }
        }
        
        response.data = custom_response_data
    
    return response

def get_error_code(exc, status_code):
    """
    Generate appropriate error codes based on exception type and status.
    """
    if isinstance(exc, Http404):
        return 'RESOURCE_NOT_FOUND'
    elif status_code == status.HTTP_400_BAD_REQUEST:
        return 'VALIDATION_ERROR'
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        return 'AUTH_INVALID_CREDENTIALS'
    elif status_code == status.HTTP_403_FORBIDDEN:
        return 'AUTH_INSUFFICIENT_PERMISSIONS'
    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return 'RATE_LIMIT_EXCEEDED'
    elif status_code >= 500:
        return 'SYSTEM_ERROR'
    else:
        return 'API_ERROR'

def get_error_message(exc, response_data):
    """
    Extract meaningful error messages from exceptions.
    """
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Handle field-specific validation errors
            messages = []
            for field, errors in exc.detail.items():
                if isinstance(errors, list):
                    messages.extend([f"{field}: {error}" for error in errors])
                else:
                    messages.append(f"{field}: {errors}")
            return "; ".join(messages)
        else:
            return str(exc.detail)
    
    return str(exc)