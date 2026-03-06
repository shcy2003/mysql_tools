"""
Database Connection Health Monitoring Module
"""
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from django.db import connection, connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


def check_db_connection(db_name: str = 'default') -> Dict[str, Any]:
    """
    Check database connection health
    
    Returns:
        dict: {
            'status': 'healthy' | 'unhealthy',
            'db_name': str,
            'response_time_ms': float,
            'timestamp': str,
            'error': str | None
        }
    """
    start_time = time.time()
    result = {
        'status': 'unhealthy',
        'db_name': db_name,
        'response_time_ms': 0,
        'timestamp': datetime.now().isoformat(),
        'error': None
    }
    
    try:
        conn = connections[db_name]
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        
        result['status'] = 'healthy'
        result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        logger.info(f"DB health check passed for {db_name}: {result['response_time_ms']}ms")
        
    except OperationalError as e:
        result['error'] = f"OperationalError: {str(e)}"
        logger.error(f"DB health check failed for {db_name}: {result['error']}")
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        logger.error(f"DB health check failed for {db_name}: {result['error']}")
    
    return result


def get_db_stats(db_name: str = 'default') -> Dict[str, Any]:
    """
    Get database connection statistics
    
    Returns:
        dict: Detailed database statistics
    """
    stats = {
        'db_name': db_name,
        'timestamp': datetime.now().isoformat(),
        'connection_info': {},
        'health_status': check_db_connection(db_name)
    }
    
    try:
        conn = connections[db_name]
        settings_dict = conn.settings_dict

        # 确保所有值都是字符串，避免 JSON 序列化问题
        def to_str(val):
            if val is None:
                return ''
            return str(val)

        stats['connection_info'] = {
            'vendor': to_str(conn.vendor),
            'display_name': to_str(settings_dict.get('DISPLAY_NAME', 'Unknown')),
            'host': to_str(settings_dict.get('HOST', 'localhost')),
            'port': to_str(settings_dict.get('PORT', 'default')),
            'database': to_str(settings_dict.get('NAME', 'unknown')),
            'user': to_str(settings_dict.get('USER', 'unknown')),
            'engine': to_str(settings_dict.get('ENGINE', 'unknown').split('.')[-1])
        }
        
        # Get MySQL specific stats if possible
        if conn.vendor == 'mysql':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SHOW STATUS LIKE 'Threads_%'")
                    threads = dict(cursor.fetchall())
                    cursor.execute("SHOW STATUS LIKE 'Connections'")
                    connections_row = cursor.fetchone()
                    stats['mysql_stats'] = {
                        'threads': threads,
                        'total_connections': connections_row[1] if connections_row else None
                    }
            except Exception as e:
                stats['mysql_stats_error'] = str(e)
                
    except Exception as e:
        stats['error'] = str(e)
        logger.error(f"Error getting DB stats: {e}")
    
    return stats


def get_all_connections_health() -> Dict[str, Any]:
    """
    Get health status for all configured database connections
    
    Returns:
        dict: Health status for all connections
    """
    result = {
        'timestamp': datetime.now().isoformat(),
        'connections': {},
        'overall_status': 'healthy'
    }
    
    for db_name in connections.databases:
        health = check_db_connection(db_name)
        result['connections'][db_name] = health
        if health['status'] != 'healthy':
            result['overall_status'] = 'unhealthy'
    
    return result
