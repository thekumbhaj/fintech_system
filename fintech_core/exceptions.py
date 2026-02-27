"""
Custom exception handlers for consistent API error responses
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error formatting
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, it's an unhandled exception
    if response is None:
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )
        
        return Response(
            {
                'error': 'Internal server error',
                'detail': str(exc) if hasattr(exc, 'detail') else 'An unexpected error occurred',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Customize the response format
    if hasattr(exc, 'detail'):
        custom_response_data = {
            'error': exc.__class__.__name__,
            'detail': response.data.get('detail', str(exc.detail)),
            'status_code': response.status_code,
        }
        
        # Add field-specific errors if they exist
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if key != 'detail':
                    custom_response_data[key] = value
        
        response.data = custom_response_data
    
    # Log the exception
    logger.warning(
        f"API exception: {exc.__class__.__name__} - {str(exc)}",
        extra={
            'status_code': response.status_code,
            'path': context.get('request').path if context.get('request') else None,
        }
    )
    
    return response


class TransactionError(Exception):
    """Base exception for transaction-related errors"""
    pass


class InsufficientBalanceError(TransactionError):
    """Raised when user has insufficient balance"""
    pass


class InvalidTransactionError(TransactionError):
    """Raised when transaction is invalid"""
    pass


class DuplicateTransactionError(TransactionError):
    """Raised when duplicate transaction is detected"""
    pass
