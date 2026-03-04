"""
Monitoring API Views
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .db_health import (
    check_db_connection,
    get_db_stats,
    get_all_connections_health
)

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def db_health_check(request):
    """
    API endpoint to check database health
    GET /api/health/db/
    """
    try:
        health = check_db_connection('default')
        status_code = 200 if health['status'] == 'healthy' else 503
        return JsonResponse(health, status=status_code)
    except Exception as e:
        logger.error(f"Error in db_health_check: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def db_health_stats(request):
    """
    API endpoint to get detailed database statistics
    GET /api/health/db/stats/
    """
    try:
        stats = get_db_stats('default')
        return JsonResponse(stats, status=200)
    except Exception as e:
        logger.error(f"Error in db_health_stats: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def all_health_check(request):
    """
    API endpoint to check health of all database connections
    GET /api/health/
    """
    try:
        health = get_all_connections_health()
        status_code = 200 if health['overall_status'] == 'healthy' else 503
        return JsonResponse(health, status=status_code)
    except Exception as e:
        logger.error(f"Error in all_health_check: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }, status=500)
