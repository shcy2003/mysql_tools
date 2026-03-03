from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import MaskingRuleForm
from .models import MaskingRule
from audit.utils import create_audit_log
from accounts.views import get_client_ip


@login_required
def masking_rule_list_view(request):
    """脱敏规则列表视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限访问脱敏规则管理！')
        return render(request, 'errors/403.html')

    rules = MaskingRule.objects.all()
    return render(request, 'desensitization/list.html', {'rules': rules})


@login_required
def masking_rule_create_view(request):
    """创建脱敏规则视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限创建脱敏规则！')
        return render(request, 'errors/403.html')

    if request.method == 'POST':
        form = MaskingRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()

            # 添加审计日志
            create_audit_log(
                user=request.user,
                action='create_masking',
                ip_address=get_client_ip(request),
                connection=rule.connection
            )

            messages.success(request, '脱敏规则创建成功！')
            return redirect('masking_rule_list')
    else:
        form = MaskingRuleForm()

    return render(request, 'desensitization/create.html', {'form': form})


@login_required
def masking_rule_edit_view(request, rule_id):
    """编辑脱敏规则视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限编辑脱敏规则！')
        return render(request, 'errors/403.html')

    rule = get_object_or_404(MaskingRule, id=rule_id)

    if request.method == 'POST':
        form = MaskingRuleForm(request.POST, instance=rule)
        if form.is_valid():
            rule = form.save()

            # 添加审计日志
            create_audit_log(
                user=request.user,
                action='update_masking',
                ip_address=get_client_ip(request),
                connection=rule.connection
            )

            messages.success(request, '脱敏规则更新成功！')
            return redirect('masking_rule_list')
    else:
        form = MaskingRuleForm(instance=rule)

    return render(request, 'desensitization/edit.html', {'form': form, 'rule': rule})


@login_required
def masking_rule_delete_view(request, rule_id):
    """删除脱敏规则视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限删除脱敏规则！')
        return render(request, 'errors/403.html')

    rule = get_object_or_404(MaskingRule, id=rule_id)

    if request.method == 'POST':
        # 添加审计日志
        create_audit_log(
            user=request.user,
            action='delete_masking',
            ip_address=get_client_ip(request),
            connection=rule.connection
        )

        rule.delete()
        messages.success(request, '脱敏规则删除成功！')
        return redirect('masking_rule_list')

    return render(request, 'desensitization/delete.html', {'rule': rule})
