"""
连接模块API视图 - 连接树、数据库列表、表列表、字段列表
"""
import re
import json
import mysql.connector
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from connections.models import MySQLConnection
from connections.pool import (
    get_connection_from_pool,
    release_connection,
)
from connections.utils import test_mysql_connection
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def api_response(code=0, message='success', data=None):
    """统一的 API 响应格式"""
    return JsonResponse({
        'code': code,
        'message': message,
        'data': data if data is not None else {}
    })


@login_required
@require_http_methods(["GET"])
def api_connection_tree(request):
    """
    获取连接树（连接->数据库->表）
    
    GET /api/connections/tree/
    
    响应:
    {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": 1,
                "name": "本地MySQL",
                "host": "localhost",
                "port": 3306,
                "databases": [
                    {
                        "name": "test_db",
                        "tables": ["users", "orders", "products"]
                    }
                ]
            }
        ]
    }
    """
    try:
        # 根据用户角色过滤连接
        if request.user.role == 'admin':
            # 管理员可以看到所有连接
            connections = MySQLConnection.objects.all()
        else:
            # 普通用户只能看到自己所属环境的连接
            user_env_ids = request.user.environments.values_list('id', flat=True)
            connections = MySQLConnection.objects.filter(environment_id__in=user_env_ids)
        
        tree_data = []
        
        for conn in connections:
            conn_data = {
                'id': conn.id,
                'name': conn.name,
                'host': conn.host,
                'port': conn.port,
                'environment': conn.environment.name if conn.environment else '',
                'databases': []
            }
            
            # 尝试获取数据库列表
            try:
                connection_params = conn.get_connection_params()
                # 移除database参数以列出所有数据库
                pool_params = connection_params.copy()
                pool_params.pop('database', None)

                # 直接创建连接，不使用连接池
                connection = mysql.connector.connect(**pool_params)
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()

                for db_row in databases:
                    db_name = db_row['Database']
                    # 跳过系统数据库
                    if db_name in ('information_schema', 'mysql', 'performance_schema', 'sys'):
                        continue

                    db_data = {
                        'name': db_name,
                        'tables': []
                    }

                    # 获取该数据库的表列表
                    try:
                        cursor.execute(f"USE `{db_name}`")
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        table_key = f"Tables_in_{db_name}"
                        for table_row in tables:
                            # MySQL 返回的列名可能是 Tables_in_dbname 或 Tables_in_{dbname}
                            table_name = table_row.get(table_key) or table_row.get('Tables_in_{}'.format(db_name))
                            if table_name:
                                # 过滤掉系统表
                                system_prefixes = ['sys_', 'mysql_', 'innodb_', 'plugin']
                                if not any(table_name.startswith(p) for p in system_prefixes):
                                    db_data['tables'].append(table_name)
                    except Exception:
                        pass  # 忽略单个数据库的错误

                    conn_data['databases'].append(db_data)

                cursor.close()
                connection.close()
                
            except Exception as e:
                # 连接失败时，保留基本连接信息，但不包含数据库详情
                conn_data['error'] = str(e)
            
            tree_data.append(conn_data)
        
        return JsonResponse({
            "code": 0,
            "message": "success",
            "data": tree_data
        })
        
    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": f"服务器内部错误: {str(e)}"
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_connection_databases(request, connection_id):
    """
    获取指定连接的数据库列表
    
    GET /api/connections/{id}/databases/
    
    响应:
    {
        "code": 0,
        "message": "success",
        "data": ["information_schema", "mysql", "test_db"]
    }
    """
    try:
        # 获取连接（所有登录用户都可以使用任意连接）
        try:
            connection = MySQLConnection.objects.get(id=connection_id)
        except MySQLConnection.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "连接不存在或无权限访问"
            }, status=404)
        
        # 获取数据库列表
        try:
            connection_params = connection.get_connection_params()
            # 移除database参数以列出所有数据库
            pool_params = connection_params.copy()
            pool_params.pop('database', None)

            # 直接创建连接，不使用连接池
            db_connection = mysql.connector.connect(**pool_params)
            cursor = db_connection.cursor(dictionary=True)
            cursor.execute("SHOW DATABASES")
            databases = [row['Database'] for row in cursor.fetchall()]

            # 过滤掉系统数据库
            system_dbs = ['performance_schema', 'information_schema', 'mysql', 'sys']
            databases = [db for db in databases if db not in system_dbs]

            cursor.close()
            db_connection.close()
            
            return JsonResponse({
                "code": 0,
                "message": "success",
                "data": databases
            })
            
        except mysql.connector.Error as e:
            return JsonResponse({
                "code": 500,
                "message": f"数据库查询错误: {str(e)}"
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": f"服务器内部错误: {str(e)}"
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_connection_tables(request, connection_id):
    """
    获取指定数据库的表列表
    
    GET /api/connections/{id}/tables/?database=xxx
    
    查询参数:
        - database: 数据库名称（必需）
    
    响应:
    {
        "code": 0,
        "message": "success",
        "data": ["users", "orders", "products"]
    }
    """
    try:
        # 获取数据库名称参数
        database_name = request.GET.get('database')
        if not database_name:
            return JsonResponse({
                "code": 400,
                "message": "缺少必需参数: database"
            }, status=400)
        
        # 验证数据库名（防止SQL注入）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', database_name):
            return JsonResponse({
                "code": 400,
                "message": f"非法的数据库名: {database_name}"
            }, status=400)
        
        # 获取连接（所有登录用户都可以使用任意连接）
        try:
            connection = MySQLConnection.objects.get(id=connection_id)
        except MySQLConnection.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "连接不存在或无权限访问"
            }, status=404)
        
        # 获取表列表
        try:
            connection_params = connection.get_connection_params()
            # 使用指定的数据库
            connection_params['database'] = database_name

            # 直接创建连接，不使用连接池
            db_connection = mysql.connector.connect(**connection_params)
            cursor = db_connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES")

            tables = []
            table_key = f"Tables_in_{database_name}"
            for row in cursor.fetchall():
                # MySQL返回的列名可能是 Tables_in_dbname 或 Tables_in_{dbname}
                table_name = row.get(table_key) or row.get(f"Tables_in_{{{database_name}}}")
                if table_name:
                    tables.append(table_name)

            # 过滤掉系统表
            system_tables_prefix = ['sys_', 'mysql_', 'innodb_', 'plugin']
            tables = [t for t in tables if not any(t.startswith(prefix) for prefix in system_tables_prefix)]

            cursor.close()
            db_connection.close()
            
            return JsonResponse({
                "code": 0,
                "message": "success",
                "data": tables
            })

        except mysql.connector.Error as e:
            return JsonResponse({
                "code": 500,
                "message": f"数据库查询错误: {str(e)}"
            }, status=500)

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": f"服务器内部错误: {str(e)}"
        }, status=500)



@login_required
@require_http_methods(["GET"])
def api_connection_columns(request, connection_id):
    """
    获取指定数据库的表字段列表

    GET /api/connections/{id}/columns/?database=xxx&table=xxx

    查询参数:
        - database: 数据库名称（必需）
        - table: 表名称（必需）

    响应:
    {
        "code": 0,
        "message": "success",
        "data": [
            {"name": "id", "type": "int", "nullable": "NO", "key": "PRI"},
            {"name": "username", "type": "varchar", "nullable": "YES", "key": ""}
        ]
    }
    """
    try:
        # 获取参数
        database_name = request.GET.get('database')
        table_name = request.GET.get('table')

        if not database_name:
            return JsonResponse({
                "code": 400,
                "message": "缺少必需参数: database"
            }, status=400)

        if not table_name:
            return JsonResponse({
                "code": 400,
                "message": "缺少必需参数: table"
            }, status=400)

        # 验证参数（防止SQL注入）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', database_name):
            return JsonResponse({
                "code": 400,
                "message": f"非法的数据库名: {database_name}"
            }, status=400)

        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return JsonResponse({
                "code": 400,
                "message": f"非法的表名: {table_name}"
            }, status=400)

        # 获取连接
        try:
            connection = MySQLConnection.objects.get(id=connection_id)
        except MySQLConnection.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "连接不存在"
            }, status=404)

        # 获取字段列表
        try:
            connection_params = connection.get_connection_params()
            connection_params['database'] = database_name

            db_connection = mysql.connector.connect(**connection_params)
            cursor = db_connection.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE `{table_name}`")

            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row.get("Field", ""),
                    "type": row.get("Type", ""),
                    "nullable": row.get("Null", ""),
                    "key": row.get("Key", ""),
                    "default": row.get("Default", ""),
                    "extra": row.get("Extra", "")
                })

            cursor.close()
            db_connection.close()

            return JsonResponse({
                "code": 0,
                "message": "success",
                "data": columns
            })

        except mysql.connector.Error as e:
            return JsonResponse({
                "code": 500,
                "message": f"数据库查询错误: {str(e)}"
            }, status=500)

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": f"服务器内部错误: {str(e)}"
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_test_connection(request):
    """
    测试数据库连接
    POST /api/connections/test/

    请求体:
    {
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "password"
    }

    返回: {"code": 0, "message": "成功信息", "data": {...}}
    """
    try:
        # 解析请求体
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return api_response(code=400, message='请求体必须是有效的 JSON')

        # 提取连接参数
        host = body.get('host')
        port = body.get('port')
        username = body.get('username')
        password = body.get('password')

        # 参数验证
        if not host:
            return api_response(code=400, message='请输入主机地址')
        if not port:
            return api_response(code=400, message='请输入端口')
        if not username:
            return api_response(code=400, message='请输入用户名')

        # 构建连接参数（不指定数据库，因为访问什么数据库由账号权限决定）
        connection_params = {
            'host': host,
            'port': int(port) if port else 3306,
            'user': username,
            'password': password or ''
        }

        # 测试连接
        success, message = test_mysql_connection(connection_params)

        # 如果提供了连接ID，更新连接状态
        connection_id = body.get('connection_id')
        if connection_id:
            try:
                connection = MySQLConnection.objects.get(id=connection_id)
                if success:
                    connection.status = 'active'
                else:
                    connection.status = 'inactive'
                connection.save()
            except MySQLConnection.DoesNotExist:
                pass

        if success:
            return api_response(code=0, message=message)
        else:
            return api_response(code=400, message=message)

    except Exception as e:
        return api_response(code=500, message=f'测试连接失败: {str(e)}')