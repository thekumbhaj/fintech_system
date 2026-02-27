"""
Health check view for monitoring
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify system status
    Returns 200 if all services are healthy
    """
    health_status = {
        'status': 'healthy',
        'database': False,
        'cache': False,
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['database'] = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status['status'] = 'unhealthy'
        health_status['database_error'] = str(e)
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        cached_value = cache.get('health_check')
        if cached_value == 'ok':
            health_status['cache'] = True
        else:
            raise Exception("Cache verification failed")
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        health_status['status'] = 'unhealthy'
        health_status['cache_error'] = str(e)
    
    # Return appropriate status code
    if health_status['status'] == 'healthy':
        return Response(health_status, status=status.HTTP_200_OK)
    else:
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
