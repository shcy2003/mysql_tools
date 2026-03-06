import logging
import mysql.connector
from mysql.connector import Error
from .models import MySQLConnection
from .pool import (
    get_connection_pool,
    get_connection_from_pool,
    release_connection,
    execute_query_with_pool,
    get_pool_stats,
    close_connection_pool,
)

# 获取日志记录器
logger = logging.getLogger(__name__)


def test_mysql_connection(connection_params):
    """测试 MySQL 连接是否正常"""
    try:
        # 创建数据库连接
        connection = mysql.connector.connect(
            host=connection_params['host'],
            port=connection_params['port'],
            database=connection_params['database'],
            user=connection_params['user'],
            password=connection_params['password']
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            cursor.close()
            return True, f"MySQL 连接成功！版本：{version[0]}"

    except Error as e:
        return False, f"MySQL 连接失败：{e}"

    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()

    return False, "连接失败，未知错误"


def get_connection_by_id(connection_id):
    """根据 ID 获取连接配置"""
    try:
        return MySQLConnection.objects.get(id=connection_id)
    except MySQLConnection.DoesNotExist:
        return None


def execute_query(connection_params, query, params=None):
    """
    执行 SQL 查询（使用连接池）
    
    Args:
        connection_params: MySQL连接参数
        query: SQL查询语句
        params: 查询参数（用于参数化查询）
    
    Returns:
        tuple: (success, results_or_error)
    """
    return execute_query_with_pool(connection_params, query, params)


def get_databases(connection_params):
    """
    获取数据库列表（使用连接池）
    
    Args:
        connection_params: MySQL连接参数（不需要database）
    
    Returns:
        list: 数据库名称列表
    
    Raises:
        Exception: 获取数据库列表失败时抛出异常
    """
    connection = None
    cursor = None
    
    try:
        # 获取不带数据库的连接（因为我们要列出所有数据库）
        pool_params = connection_params.copy()
        pool_params.pop('database', None)  # 移除数据库参数
        
        connection = get_connection_from_pool(pool_params)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SHOW DATABASES")
        databases = [row['Database'] for row in cursor.fetchall()]
        
        return databases

    except Error as e:
        logger.error(f"获取数据库列表失败: {e}")
        raise Exception(f"获取数据库列表失败: {str(e)}")
    except Exception as e:
        logger.error(f"获取数据库列表时发生错误: {e}")
        raise Exception(f"获取数据库列表失败: {str(e)}")
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            release_connection(connection)


def get_tables(connection, database):
    """
    获取指定数据库的表列表

    Args:
        connection: MySQLConnection 模型实例
        database: 数据库名称

    Returns:
        list: 表名列表
    """
    connection_params = connection.get_connection_params()
    connection_params['database'] = database

    conn = None
    cursor = None
    try:
        # 直接创建新连接，不使用连接池（因为数据库参数不同）
        conn = mysql.connector.connect(**connection_params)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES")
        tables = [row[f"Tables_in_{database}"] for row in cursor.fetchall()]
        return tables
    except Error as e:
        logger.error(f"获取表列表失败: {e}")
        raise Exception(f"获取表列表失败: {str(e)}")
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn and conn.is_connected():
            conn.close()


import re

def get_columns(connection_params, table_name):
    """
    获取表的列信息（使用表名白名单验证防止SQL注入）
    
    Args:
        connection_params: 数据库连接参数
        table_name: 表名
    
    Returns:
        tuple: (success, columns_or_error)
    """
    # 白名单验证表名（只允许字母数字下划线）
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        return False, f"非法的表名: {table_name}"
    
    try:
        connection = mysql.connector.connect(**connection_params)
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            # 使用参数化查询执行（注意：表名不能使用占位符，已通过白名单验证）
            # 对于DESCRIBE语句，我们使用安全的字符串拼接，因为表名已经过白名单验证
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            cursor.close()
            connection.close()
            return True, columns

    except Error as e:
        return False, str(e)

    return False, "获取列信息失败"