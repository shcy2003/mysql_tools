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

    # 获取全局脱敏规则数量
    from desensitization.models import MaskingRule
    masking_rules_count = MaskingRule.objects.count()

    return render(request, 'queries/list.html', {
        'connections': connections,
        'masking_rules_count': masking_rules_count
    })


@login_required
def sql_query_view(request):
    """SQL 查询视图（重定向到新页面）"""
    return redirect('queries:sql_query_new')


# Note: visual_query_view has been removed as per project requirements
# 可视化查询功能已不再使用，请使用新的 SQL 查询界面 API

@login_required
def query_history_view(request):
    """查询历史视图（支持筛选）"""
    # 基础查询：管理员查看所有，普通用户只看自己的
    if request.user.role == 'admin':
        history = QueryHistory.objects.all()
    else:
        history = QueryHistory.objects.filter(user=request.user)

    # 获取所有用户和连接（用于筛选下拉框）
    from accounts.models import User
    all_users = User.objects.all()
    from connections.models import MySQLConnection
    all_connections = MySQLConnection.objects.all()

    # 筛选条件
    filter_user_id = request.GET.get('user')
    filter_connection_id = request.GET.get('connection')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sql_keyword = request.GET.get('sql_keyword')
    min_execution_time = request.GET.get('min_execution_time')

    if filter_user_id:
        history = history.filter(user_id=filter_user_id)
    if filter_connection_id:
        history = history.filter(connection_id=filter_connection_id)
    if start_date and end_date:
        from django.utils import timezone
        import datetime
        start_datetime = timezone.make_aware(datetime.datetime.strptime(start_date, '%Y-%m-%d'))
        end_datetime = timezone.make_aware(datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1))
        history = history.filter(created_at__range=(start_datetime, end_datetime))
    if sql_keyword:
        history = history.filter(sql__icontains=sql_keyword)
    if min_execution_time:
        try:
            min_time = float(min_execution_time)
            # 转换为毫秒（因为数据库中存储的是毫秒）
            min_time_ms = min_time * 1000
            history = history.filter(execution_time__gte=min_time_ms)
        except ValueError:
            pass

    # 排序
    history = history.order_by('-created_at')

    # 分页
    from django.core.paginator import Paginator
    paginator = Paginator(history, 20)
    page = request.GET.get('page')
    history_page = paginator.get_page(page)

    context = {
        'history': history_page,
        'all_users': all_users,
        'all_connections': all_connections,
        'filter_user': filter_user_id,
        'filter_connection': filter_connection_id,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'filter_sql_keyword': sql_keyword,
        'filter_min_execution_time': min_execution_time,
    }

    return render(request, 'queries/history.html', context)


# Note: visual_query_view has been removed as per project requirements


def get_available_connections(user):
    """获取用户可以使用的连接"""
    return MySQLConnection.objects.all()


@login_required
def sql_query_new_view(request):
    """新的 SQL 查询界面（支持连接树和 AJAX 查询）"""
    return render(request, 'queries/sql_query_new.html', {})


@login_required
def saved_queries_view(request):
    """保存的SQL查询视图"""
    from .models import SavedQuery
    queries = SavedQuery.objects.filter(user=request.user).select_related('connection').order_by('-updated_at')
    return render(request, 'queries/saved_queries.html', {
        'queries': queries
    })
