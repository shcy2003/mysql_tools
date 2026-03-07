from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import AuditLog


@login_required
def audit_log_list_view(request):
    """审计日志列表视图（仅管理员可以访问）"""
    if request.user.role != 'admin':
        from django.contrib import messages
        messages.error(request, '您没有权限访问审计日志！')
        return render(request, 'errors/403.html')

    logs = AuditLog.objects.all()

    # 过滤条件
    action = request.GET.get('action')
    user_id = request.GET.get('user')
    connection_id = request.GET.get('connection')
    date_range = request.GET.get('date_range')
    min_time = request.GET.get('min_time')

    if min_time:
        try:
            # 转换为毫秒（execution_time 字段单位是ms）
            min_time_ms = float(min_time) * 1000
            logs = logs.filter(execution_time__gte=min_time_ms)
        except:
            pass

    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if connection_id:
        logs = logs.filter(connection_id=connection_id)

    # 处理时间范围
    if date_range:
        from django.utils import timezone
        import datetime
        now = timezone.now()
        if date_range == '1h':
            start_datetime = now - datetime.timedelta(hours=1)
        elif date_range == '3h':
            start_datetime = now - datetime.timedelta(hours=3)
        elif date_range == '6h':
            start_datetime = now - datetime.timedelta(hours=6)
        elif date_range == '12h':
            start_datetime = now - datetime.timedelta(hours=12)
        elif date_range == '1d':
            start_datetime = now - datetime.timedelta(days=1)
        elif date_range == '3d':
            start_datetime = now - datetime.timedelta(days=3)
        elif date_range == '1w':
            start_datetime = now - datetime.timedelta(weeks=1)
        elif date_range == '1m':
            start_datetime = now - datetime.timedelta(days=30)
        else:
            start_datetime = None

        if start_datetime:
            logs = logs.filter(created_at__gte=start_datetime)

    # 分页
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    # 获取所有用户和连接信息（用于筛选）
    from accounts.models import User
    all_users = User.objects.all()
    from connections.models import MySQLConnection
    all_connections = MySQLConnection.objects.all()

    context = {
        'logs': logs_page,
        'all_users': all_users,
        'all_connections': all_connections,
        'selected_action': action,
        'selected_user': user_id,
        'selected_connection': connection_id,
        'selected_date_range': date_range,
        'selected_min_time': min_time,
    }

    return render(request, 'audit/list.html', context)
