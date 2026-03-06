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

        if not connection_id or not sql:
            messages.error(request, '请选择连接并输入 SQL 语句')
            return render(request, 'queries/sql_query.html', {
                'connections': get_available_connections(request.user)
            })

        connection = get_object_or_404(MySQLConnection, id=connection_id)

        # 检查权限：只有管理员或创建者可以使用此连接查询
        if request.user.role != 'admin' and connection.created_by != request.user:
            messages.error(request, '您没有权限使用此连接！')
            return redirect('queries:sql_query')

        # 检查 SQL 是否为 SELECT
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith('SELECT'):
            messages.error(request, '仅支持 SELECT 查询语句！')
            return render(request, 'queries/sql_query.html', {
                'connections': get_available_connections(request.user),
                'selected_connection': connection_id,
                'sql': sql
            })

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
            'result': result if success else None,
            'execution_time': execution_time,
            'success': success,
            'error': None if success else result
        })
    else:
        return render(request, 'queries/sql_query.html', {
            'connections': get_available_connections(request.user)
        })


# Note: visual_query_view has been removed as per project requirements
# 可视化查询功能已不再使用，请使用新的 SQL 查询界面 API

@login_required
def query_history_view(request):
    """查询历史视图"""
    history = QueryHistory.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'queries/history.html', {'history': history})


# Note: visual_query_view has been removed as per project requirements


def get_available_connections(user):
    """获取用户可以使用的连接"""
    if user.role == 'admin':
        return MySQLConnection.objects.all()
    else:
        return MySQLConnection.objects.filter(created_by=user)


@login_required
def sql_query_new_view(request):
    """新的 SQL 查询界面（支持连接树和 AJAX 查询）"""
    return render(request, 'queries/sql_query_new.html', {})
