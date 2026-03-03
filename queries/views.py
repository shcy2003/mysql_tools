import re
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from connections.models import MySQLConnection
from connections.utils import get_tables, get_columns, get_databases
from .utils import run_query
from .models import QueryHistory


@login_required
def query_list_view(request):
    """查询列表视图（首页）"""
    # 获取用户可以访问的连接
    if request.user.role == 'admin':
        connections = MySQLConnection.objects.all()
    else:
        connections = MySQLConnection.objects.filter(created_by=request.user)

    return render(request, 'queries/list.html', {'connections': connections})


@login_required
def sql_query_view(request):
    """SQL 查询视图"""
    if request.method == 'POST':
        connection_id = request.POST.get('connection')
        sql = request.POST.get('sql')

        connection = get_object_or_404(MySQLConnection, id=connection_id)

        # 检查权限：只有管理员或创建者可以使用此连接查询
        if request.user.role != 'admin' and connection.created_by != request.user:
            messages.error(request, '您没有权限使用此连接！')
            return redirect('sql_query')

        success, result, execution_time = run_query(
            connection, sql, request.user, request)

        if success:
            messages.success(
                request, f'查询成功！共返回 {len(result)} 条记录，耗时 {execution_time:.2f}ms')
        else:
            messages.error(request, f'查询失败：{result}')

        return render(request, 'queries/sql_query.html', {
            'connections': get_available_connections(request.user),
            'selected_connection': connection_id,
            'sql': sql,
            'result': result,
            'execution_time': execution_time,
            'success': success
        })
    else:
        return render(request, 'queries/sql_query.html', {
            'connections': get_available_connections(request.user)
        })


@login_required
def visual_query_view(request):
    """可视化查询视图"""
    connections = get_available_connections(request.user)
    selected_connection = request.GET.get('connection')
    tables = []
    selected_table = request.GET.get('table')
    columns = []
    result = None
    execution_time = None
    success = False
    sql = None

    if selected_connection:
        connection = get_object_or_404(MySQLConnection, id=selected_connection)
        tables = get_tables(connection.get_connection_params())[1]

    if selected_table:
        connection = get_object_or_404(MySQLConnection, id=selected_connection)
        columns = get_columns(connection.get_connection_params(), selected_table)[1]

    if request.method == 'POST':
        connection_id = request.POST.get('connection')
        table_name = request.POST.get('table')
        selected_fields = request.POST.getlist('fields')
        conditions = parse_conditions(request.POST)

        connection = get_object_or_404(MySQLConnection, id=connection_id)
        
        # 使用安全的参数化查询
        try:
            sql, params = build_query(table_name, selected_fields, conditions)
            success, result, execution_time = run_query_with_params(connection, sql, params, request.user, request)
        except ValueError as e:
            success = False
            result = str(e)
            execution_time = 0

        if success:
            messages.success(
                request, f'查询成功！共返回 {len(result)} 条记录，耗时 {execution_time:.2f}ms')
        else:
            messages.error(request, f'查询失败：{result}')

    return render(request, 'queries/visual_query.html', {
        'connections': connections,
        'selected_connection': selected_connection,
        'tables': tables,
        'selected_table': selected_table,
        'columns': columns,
        'result': result,
        'execution_time': execution_time,
        'success': success,
        'sql': sql
    })


@login_required
def query_history_view(request):
    """查询历史视图"""
    history = QueryHistory.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'queries/history.html', {'history': history})


def get_available_connections(user):
    """获取用户可以使用的连接"""
    if user.role == 'admin':
        return MySQLConnection.objects.all()
    else:
        return MySQLConnection.objects.filter(created_by=user)


def parse_conditions(post_data):
    """解析查询条件"""
    conditions = []
    condition_count = int(post_data.get('condition_count', 0))

    for i in range(condition_count):
        field = post_data.get(f'condition_field_{i}')
        operator = post_data.get(f'condition_operator_{i}')
        value = post_data.get(f'condition_value_{i}')

        if field and operator and value:
            conditions.append({
                'field': field,
                'operator': operator,
                'value': value
            })

    return conditions


def build_query(table_name, fields, conditions):
    """
    构建 SQL 查询（使用参数化查询防止SQL注入）
    
    Args:
        table_name: 表名
        fields: 字段列表
        conditions: 查询条件列表
    
    Returns:
        tuple: (sql_string, params_list)
    
    Raises:
        ValueError: 当输入包含非法字符时
    """
    # 白名单验证字段名（只允许字母数字下划线）
    def validate_identifier(name):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            raise ValueError(f"非法的字段名或表名: {name}")
        return name
    
    # 验证表名
    validate_identifier(table_name)
    
    # 验证所有字段名
    safe_fields = []
    for field in fields:
        validate_identifier(field)
        safe_fields.append(field)
    
    select_clause = ', '.join(safe_fields)
    from_clause = table_name
    where_clause = ''
    params = []

    if conditions:
        where_conditions = []
        for cond in conditions:
            # 验证字段名
            validate_identifier(cond['field'])
            
            # 白名单验证操作符
            allowed_operators = ['=', '!=', '>', '<', '>=', '<=', 'like', 'in']
            if cond['operator'].lower() not in allowed_operators:
                raise ValueError(f"非法的操作符: {cond['operator']}")
            
            if cond['operator'].lower() == 'in':
                # IN 操作符需要多个占位符
                values = cond['value'].split(',')
                placeholders = ', '.join(['%s'] * len(values))
                where_conditions.append(f"{cond['field']} IN ({placeholders})")
                params.extend([v.strip() for v in values])
            elif cond['operator'].lower() == 'like':
                # LIKE 操作符使用占位符
                where_conditions.append(f"{cond['field']} LIKE %s")
                params.append(f"%{cond['value']}%")
            else:
                # 其他操作符使用占位符
                where_conditions.append(f"{cond['field']} {cond['operator']} %s")
                params.append(cond['value'])

        where_clause = ' WHERE ' + ' AND '.join(where_conditions)

    sql = f"SELECT {select_clause} FROM {from_clause}{where_clause}"
    return sql, params


def run_query_with_params(connection, sql, params, user, request):
    """
    使用参数化查询执行SQL
    
    Args:
        connection: MySQLConnection对象
        sql: SQL语句（含占位符）
        params: 参数列表
        user: 用户对象
        request: 请求对象
    
    Returns:
        tuple: (success, result, execution_time)
    """
    import mysql.connector
    from mysql.connector import Error
    import time
    
    start_time = time.time()
    
    try:
        connection_params = connection.get_connection_params()
        conn = mysql.connector.connect(**connection_params)
        
        if conn.is_connected():
            cursor = conn.cursor(dictionary=True)
            # 使用参数化查询执行
            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            execution_time = (time.time() - start_time) * 1000
            
            # 记录查询历史（异步或同步）
            try:
                QueryHistory.objects.create(
                    user=user,
                    connection=connection,
                    sql_query=sql,
                    result_count=len(results),
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except Exception:
                pass  # 记录历史失败不应影响查询结果
            
            return True, results, execution_time
            
    except Error as e:
        execution_time = (time.time() - start_time) * 1000
        return False, str(e), execution_time
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return False, f"查询执行错误: {str(e)}", execution_time
    
    return False, "查询失败，未知错误", 0
