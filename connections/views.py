from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import MySQLConnectionForm
from .models import MySQLConnection
from .utils import test_mysql_connection
from audit.utils import create_audit_log


@login_required
def connection_list_view(request):
    """连接列表视图"""
    # 所有登录用户都可以查看所有连接
    connections = MySQLConnection.objects.all()
    return render(request, 'connections/list.html', {'connections': connections})


@login_required
def connection_create_view(request):
    """创建连接视图"""
    if request.method == 'POST':
        form = MySQLConnectionForm(request.POST)
        if form.is_valid():
            connection = form.save(commit=False)
            connection.created_by = request.user
            connection.save()

            # 测试连接
            success, message = test_mysql_connection(
                connection.get_connection_params())
            if not success:
                connection.delete()
                messages.error(request, f'连接创建失败：{message}')
                return render(request, 'connections/create.html', {'form': form})

            # 添加审计日志
            from accounts.views import get_client_ip
            create_audit_log(
                user=request.user,
                action='create_connection',
                ip_address=get_client_ip(request),
                connection=connection
            )

            messages.success(request, '连接创建成功！')
            return redirect('connections:connection_list')
    else:
        form = MySQLConnectionForm()

    return render(request, 'connections/create.html', {'form': form})


@login_required
def connection_edit_view(request, connection_id):
    """编辑连接视图"""
    connection = get_object_or_404(MySQLConnection, id=connection_id)

    # 检查权限：只有管理员或创建者可以编辑
    if request.user.role != 'admin' and connection.created_by != request.user:
        messages.error(request, '您没有权限编辑此连接！')
        return redirect('connections:connection_list')

    if request.method == 'POST':
        form = MySQLConnectionForm(request.POST, instance=connection)
        if form.is_valid():
            connection = form.save()

            # 测试连接
            success, message = test_mysql_connection(
                connection.get_connection_params())
            if not success:
                messages.error(request, f'连接更新失败：{message}')
                return render(request, 'connections/edit.html', {'form': form, 'connection': connection})

            # 添加审计日志
            from accounts.views import get_client_ip
            create_audit_log(
                user=request.user,
                action='update_connection',
                ip_address=get_client_ip(request),
                connection=connection
            )

            messages.success(request, '连接更新成功！')
            return redirect('connections:connection_list')
    else:
        form = MySQLConnectionForm(instance=connection)

    return render(request, 'connections/edit.html', {'form': form, 'connection': connection})


@login_required
def connection_delete_view(request, connection_id):
    """删除连接视图"""
    connection = get_object_or_404(MySQLConnection, id=connection_id)

    # 检查权限：只有管理员或创建者可以删除
    if request.user.role != 'admin' and connection.created_by != request.user:
        messages.error(request, '您没有权限删除此连接！')
        return redirect('connections:connection_list')

    if request.method == 'POST':
        # 添加审计日志
        from accounts.views import get_client_ip
        create_audit_log(
            user=request.user,
            action='delete_connection',
            ip_address=get_client_ip(request),
            connection=connection
        )

        connection.delete()
        messages.success(request, '连接删除成功！')
        return redirect('connections:connection_list')

    return render(request, 'connections/delete.html', {'connection': connection})


@login_required
def connection_test_view(request, connection_id):
    """测试连接视图"""
    connection = get_object_or_404(MySQLConnection, id=connection_id)

    # 检查权限：只有管理员或创建者可以测试连接
    if request.user.role != 'admin' and connection.created_by != request.user:
        messages.error(request, '您没有权限测试此连接！')
        return redirect('connections:connection_list')

    success, message = test_mysql_connection(
        connection.get_connection_params())

    if success:
        messages.success(request, message)
        connection.status = 'active'
    else:
        messages.error(request, message)
        connection.status = 'inactive'

    connection.save()
    return redirect('connections:connection_list')


# ==================== API 视图 ====================

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


def api_response(code=0, message='success', data=None):
    """统一的 API 响应格式"""
    return JsonResponse({
        'code': code,
        'message': message,
        'data': data if data is not None else {}
    })


@login_required
@require_http_methods(['GET'])
def api_connection_tree(request):
    """
    获取连接树 API
    GET /api/connections/tree/

    返回所有连接，以及每个连接下的数据库和表结构。
    """
    try:
        # 获取所有连接（所有登录用户都可以看到所有连接）
        connections = MySQLConnection.objects.all()

        tree_data = []
        for conn in connections:
            conn_data = {
                'id': conn.id,
                'name': conn.name,
                'host': conn.host,
                'port': conn.port,
                'databases': []
            }
            
            # 尝试获取数据库列表
            try:
                from .utils import get_databases, get_tables
                databases = get_databases(conn.get_connection_params())
                for db_name in databases:
                    db_data = {
                        'name': db_name,
                        'tables': []
                    }
                    # 尝试获取表列表
                    try:
                        tables = get_tables(conn, db_name)
                        db_data['tables'] = tables
                    except Exception as e:
                        # 获取表列表失败，继续
                        pass
                    conn_data['databases'].append(db_data)
            except Exception as e:
                # 获取数据库列表失败，继续
                pass
            
            tree_data.append(conn_data)

        return api_response(data=tree_data)

    except Exception as e:
        return api_response(code=500, message=f'获取连接树失败: {str(e)}')


@login_required
@require_http_methods(['GET'])
def api_connection_databases(request, connection_id):
    """
    获取指定连接的所有数据库
    GET /api/connections/{id}/databases/
    """
    try:
        connection = get_object_or_404(MySQLConnection, id=connection_id)

        # 所有登录用户都可以访问所有连接
        from .utils import get_databases
        try:
            databases = get_databases(connection.get_connection_params())
            return api_response(data=databases)
        except Exception as e:
            return api_response(code=500, message=f'获取数据库列表失败: {str(e)}')
    
    except Exception as e:
        return api_response(code=500, message=f'获取数据库列表失败: {str(e)}')


@login_required
@require_http_methods(['GET'])
def api_connection_tables(request, connection_id):
    """
    获取指定数据库的所有表
    GET /api/connections/{id}/tables/?database=xxx
    """
    try:
        database = request.GET.get('database')
        if not database:
            return api_response(code=400, message='缺少 database 参数')

        connection = get_object_or_404(MySQLConnection, id=connection_id)

        # 所有登录用户都可以访问所有连接
        from .utils import get_tables
        tables = get_tables(connection, database)
        
        return api_response(data=tables)
    
    except Exception as e:
        return api_response(code=500, message=f'获取表列表失败: {str(e)}')


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_query_execute(request):
    """
    执行 SQL 查询
    POST /api/queries/execute/
    
    请求体:
    {
        "connection_id": 1,
        "sql": "SELECT * FROM users WHERE age > 18"
    }
    
    仅支持 SELECT 语句，最多返回 10 条记录。
    """
    try:
        # 解析请求体
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return api_response(code=400, message='请求体必须是有效的 JSON')
        
        connection_id = body.get('connection_id')
        sql = body.get('sql', '').strip()
        
        # 参数验证
        if not connection_id:
            return api_response(code=400, message='缺少 connection_id 参数')
        if not sql:
            return api_response(code=400, message='缺少 sql 参数')
        
        # 获取连接
        try:
            connection = MySQLConnection.objects.get(id=connection_id)
        except MySQLConnection.DoesNotExist:
            return api_response(code=404, message='连接不存在')
        
        # 检查权限
        if request.user.role != 'admin' and connection.created_by != request.user:
            return api_response(code=403, message='没有权限使用此连接')
        
        # 验证 SQL 语句（只允许 SELECT）
        sql_upper = sql.upper().lstrip()
        if not sql_upper.startswith('SELECT'):
            return api_response(code=400, message='只允许执行 SELECT 查询')
        
        # 执行查询
        from .utils import run_query
        success, result, execution_time = run_query(connection, sql, request.user, request)
        
        if not success:
            return api_response(code=400, message=f'查询执行失败: {result}')
        
        # 限制返回行数（最多10条）
        row_count = len(result)
        limited = False
        if row_count > 10:
            result = result[:10]
            limited = true
        
        # 提取列名和行数据
        columns = result[0].keys() if result else []
        rows = []
        for row in result:
            row_data = {}
            for col in columns:
                row_data[col] = row[col]
            rows.append(row_data)
        
        return api_response(data={
            'columns': list(columns),
            'rows': rows,
            'row_count': row_count,
            'execution_time_ms': execution_time,
            'limited': limited
        })
    
    except Exception as e:
        import traceback
        print(f"API执行查询出错: {str(e)}")
        print(traceback.format_exc())
        return api_response(code=500, message=f'服务器内部错误: {str(e)}')


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
        "database": "test_db",
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
        database = body.get('database')
        username = body.get('username')
        password = body.get('password')

        # 参数验证
        if not host:
            return api_response(code=400, message='请输入主机地址')
        if not port:
            return api_response(code=400, message='请输入端口')
        if not database:
            return api_response(code=400, message='请输入数据库名称')
        if not username:
            return api_response(code=400, message='请输入用户名')

        # 构建连接参数
        connection_params = {
            'host': host,
            'port': int(port) if port else 3306,
            'database': database,
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
        import traceback
        print(f"API测试连接出错: {str(e)}")
        print(traceback.format_exc())
        return api_response(code=500, message=f'测试连接失败: {str(e)}')