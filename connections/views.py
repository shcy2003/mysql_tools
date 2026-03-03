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
    # 只有管理员可以查看所有连接
    if request.user.role == 'admin':
        connections = MySQLConnection.objects.all()
    else:
        connections = MySQLConnection.objects.filter(created_by=request.user)

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
            return redirect('connection_list')
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
        return redirect('connection_list')

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
            return redirect('connection_list')
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
        return redirect('connection_list')

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
        return redirect('connection_list')

    return render(request, 'connections/delete.html', {'connection': connection})


@login_required
def connection_test_view(request, connection_id):
    """测试连接视图"""
    connection = get_object_or_404(MySQLConnection, id=connection_id)

    # 检查权限：只有管理员或创建者可以测试连接
    if request.user.role != 'admin' and connection.created_by != request.user:
        messages.error(request, '您没有权限测试此连接！')
        return redirect('connection_list')

    success, message = test_mysql_connection(
        connection.get_connection_params())

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('connection_list')