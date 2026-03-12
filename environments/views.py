from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Environment
from .forms import EnvironmentForm
from audit.utils import create_audit_log
import json


def get_client_ip(request):
    """获取客户端IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def environment_list(request):
    """环境列表视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    environments = Environment.objects.all()
    return render(request, 'environments/list.html', {'environments': environments})


@login_required
def environment_create(request):
    """创建环境视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    if request.method == 'POST':
        form = EnvironmentForm(request.POST)
        if form.is_valid():
            form.save()
            create_audit_log(
                user=request.user,
                action='create_environment',
                ip_address=get_client_ip(request)
            )
            messages.success(request, '环境创建成功！')
            return redirect('environments:environment_list')
    else:
        form = EnvironmentForm()

    return render(request, 'environments/form.html', {'form': form, 'action': '创建'})


@login_required
def environment_edit(request, env_id):
    """编辑环境视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    env = get_object_or_404(Environment, id=env_id)

    if request.method == 'POST':
        form = EnvironmentForm(request.POST, instance=env)
        if form.is_valid():
            form.save()
            create_audit_log(
                user=request.user,
                action='update_environment',
                ip_address=get_client_ip(request)
            )
            messages.success(request, '环境更新成功！')
            return redirect('environments:environment_list')
    else:
        form = EnvironmentForm(instance=env)

    return render(request, 'environments/form.html', {'form': form, 'action': '编辑', 'env': env})


@login_required
def environment_delete(request, env_id):
    """删除环境视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    env = get_object_or_404(Environment, id=env_id)

    if request.method == 'POST':
        env_name = env.name
        env.delete()
        create_audit_log(
            user=request.user,
            action='delete_environment',
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'环境 "{env_name}" 删除成功！')
        return redirect('environments:environment_list')

    return render(request, 'environments/confirm_delete.html', {'env': env})
