from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import LoginForm, UserForm
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
            # 表单验证失败
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
    return redirect('accounts:login')


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


# ===== 用户管理视图 =====
@login_required
def user_list(request):
    """用户列表视图（仅管理员）"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_create(request):
    """创建用户视图（仅管理员）"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()

            # 手动保存多对多关系（environments）
            from environments.models import Environment
            env_ids = request.POST.getlist('environments')
            if env_ids:
                environments = Environment.objects.filter(id__in=env_ids)
            else:
                environments = Environment.objects.none()
            user.environments.set(environments)

            messages.success(request, f'用户 {user.username} 创建成功！')
            return redirect('accounts:user_list')
    else:
        form = UserForm()

    return render(request, 'accounts/user_form.html', {'form': form, 'title': '创建用户', 'edit_user': None})


@login_required
def user_edit(request, user_id):
    """编辑用户视图（仅管理员）"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                updated_user.set_password(password)
            updated_user.save()

            # 手动保存多对多关系（environments）
            from environments.models import Environment
            env_ids = request.POST.getlist('environments')
            if env_ids:
                environments = Environment.objects.filter(id__in=env_ids)
            else:
                environments = Environment.objects.none()
            updated_user.environments.set(environments)

            messages.success(request, f'用户 {updated_user.username} 更新成功！')
            return redirect('accounts:user_list')
    else:
        form = UserForm(instance=user)

    return render(request, 'accounts/user_form.html', {'form': form, 'title': '编辑用户', 'edit_user': user})


@login_required
def user_delete(request, user_id):
    """删除用户视图（仅管理员）"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问此页面！')
        return redirect('queries:query_list')

    # 不能删除自己
    if request.user.id == user_id:
        messages.error(request, '不能删除当前登录用户！')
        return redirect('accounts:user_list')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'用户 {username} 删除成功！')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_confirm_delete.html', {'edit_user': user})
