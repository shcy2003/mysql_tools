from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import LoginForm
from .models import User


def login_view(request):
    """登录视图"""
    if request.user.is_authenticated:
        return redirect('queries:query_list')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # 更新用户登录信息
                user.last_login = timezone.now()
                user.last_login_ip = get_client_ip(request)
                user.login_count += 1
                user.save()

                # 添加登录审计日志
                from audit.utils import create_audit_log
                create_audit_log(
                    user=user,
                    action='login',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, '登录成功！')
                return redirect('queries:query_list')
            else:
                messages.error(request, '用户名或密码错误！')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """登出视图"""
    # 添加登出审计日志
    from audit.utils import create_audit_log
    create_audit_log(
        user=request.user,
        action='logout',
        ip_address=get_client_ip(request)
    )

    logout(request)
    messages.success(request, '已成功登出！')
    return redirect('login')


@login_required
def profile_view(request):
    """用户个人信息视图"""
    return render(request, 'accounts/profile.html', {'user': request.user})


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
