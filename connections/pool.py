"""
MySQL连接池管理模块
提供连接池的创建、获取、释放和管理功能
"""
import threading
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling


# 全局连接池字典
_connection_pools = {}
_pools_lock = threading.Lock()


def _get_pool_key(connection_params):
    """生成连接池的唯一键（使用哈希避免长度超限）"""
    import hashlib
    host = connection_params.get('host', 'localhost')
    port = connection_params.get('port', 3306)
    user = connection_params.get('user', '')
    # 使用主机名+端口+用户的哈希值作为唯一标识
    key_str = f"{host}:{port}:{user}"
    key_hash = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return key_hash


def get_connection_pool(connection_params, pool_size=20):
    """
    获取或创建连接池

    Args:
        connection_params: MySQL连接参数
        pool_size: 连接池大小，默认20

    Returns:
        MySQL连接池对象
    """
    pool_key = _get_pool_key(connection_params)

    with _pools_lock:
        if pool_key not in _connection_pools:
            # 创建新的连接池
            pool_config = {
                'pool_name': f"pool_{pool_key}",
                'pool_size': pool_size,
                'host': connection_params.get('host', 'localhost'),
                'port': connection_params.get('port', 3306),
                'user': connection_params.get('user', ''),
                'password': connection_params.get('password', ''),
            }

            # 如果指定了数据库，添加到配置
            if connection_params.get('database'):
                pool_config['database'] = connection_params['database']
            
            try:
                _connection_pools[pool_key] = pooling.MySQLConnectionPool(**pool_config)
            except Error as e:
                raise Exception(f"创建连接池失败: {e}")
        
        return _connection_pools[pool_key]


def get_connection_from_pool(connection_params):
    """
    从连接池获取连接
    
    Args:
        connection_params: MySQL连接参数
    
    Returns:
        MySQL连接对象
    """
    pool = get_connection_pool(connection_params)
    try:
        return pool.get_connection()
    except Error as e:
        raise Exception(f"从连接池获取连接失败: {e}")


def release_connection(connection):
    """
    释放连接回连接池
    
    Args:
        connection: MySQL连接对象
    """
    if connection:
        try:
            connection.close()
        except:
            pass


def execute_query_with_pool(connection_params, query, params=None):
    """
    使用连接池执行SQL查询
    
    Args:
        connection_params: MySQL连接参数
        query: SQL查询语句
        params: 查询参数（用于参数化查询）
    
    Returns:
        tuple: (success, results_or_error)
    """
    connection = None
    cursor = None
    
    try:
        connection = get_connection_from_pool(connection_params)
        cursor = connection.cursor(dictionary=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        return True, results
        
    except Error as e:
        return False, str(e)
    except Exception as e:
        return False, f"查询执行错误: {str(e)}"
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            release_connection(connection)


def get_pool_stats():
    """
    获取连接池统计信息
    
    Returns:
        dict: 连接池统计信息
    """
    with _pools_lock:
        stats = {}
        for pool_key, pool in _connection_pools.items():
            try:
                stats[pool_key] = {
                    'pool_name': pool.pool_name,
                    'pool_size': pool.pool_size,
                }
            except:
                stats[pool_key] = {'error': '无法获取统计信息'}
        return stats


def close_connection_pool(connection_params=None):
    """
    关闭连接池
    
    Args:
        connection_params: MySQL连接参数，如果为None则关闭所有连接池
    """
    with _pools_lock:
        if connection_params is None:
            # 关闭所有连接池
            for pool in _connection_pools.values():
                try:
                    pool._remove_connections()
                except:
                    pass
            _connection_pools.clear()
        else:
            # 关闭指定连接池
            pool_key = _get_pool_key(connection_params)
            if pool_key in _connection_pools:
                try:
                    _connection_pools[pool_key]._remove_connections()
                except:
                    pass
                del _connection_pools[pool_key]
