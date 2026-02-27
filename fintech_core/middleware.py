"""
Custom middleware for request logging and monitoring
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and their response times
    """
    
    def process_request(self, request):
        """Mark the time when request comes in"""
        request.start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                'ip': self.get_client_ip(request),
            }
        )
        return None
    
    def process_response(self, request, response):
        """Calculate and log request duration"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            logger.info(
                f"Request completed: {request.method} {request.path} - Status: {response.status_code} - Duration: {duration:.2f}s",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    'ip': self.get_client_ip(request),
                }
            )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
