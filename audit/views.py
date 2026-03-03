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
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if connection_id:
        logs = logs.filter(connection_id=connection_id)
    if start_date and end_date:
        from django.utils import timezone
        import datetime
        start_datetime = timezone.make_aware(datetime.datetime.strptime(start_date, '%Y-%m-%d'))
        end_datetime = timezone.make_aware(datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1))
        logs = logs.filter(created_at__range=(start_datetime, end_datetime))

    # 分页
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    # 获取所有用户和连接信息（用于筛选）
    from django.contrib.auth.models import User
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
        'selected_start_date': start_date,
        'selected_end_date': end_date,
    }

    return render(request, 'audit/list.html', context)
