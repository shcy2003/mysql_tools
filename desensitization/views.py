from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import MaskingRuleForm
from .models import MaskingRule
from audit.utils import create_audit_log
from accounts.views import get_client_ip
import json


@login_required
def masking_rule_list_view(request):
    """脱敏规则列表视图（所有登录用户可查看）"""
    rules = MaskingRule.objects.all()
    return render(request, 'desensitization/list.html', {'rules': rules})


@login_required
def masking_rule_create_view(request):
    """创建脱敏规则视图"""
    if request.user.role != 'admin':
        messages.error(request, '您没有权限创建脱敏规则！')
        return render(request, 'errors/403.html')

    if request.method == 'POST':
        # 从POST数据中获取column_names（JSON字符串）
        column_names_json = request.POST.get('column_names_json', '[]')
        try:
            column_names = json.loads(column_names_json)
        except:
            column_names = []

        # 手动构建数据
        data = {
            'name': request.POST.get('name'),
            'column_names': column_names,
            'masking_type': request.POST.get('masking_type'),
            'masking_params': request.POST.get('masking_params'),
        }

        form = MaskingRuleForm(data)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.created_by = request.user
            rule.save()

            # 添加审计日志
            create_audit_log(
                user=request.user,
                action='create_masking',
                ip_address=get_client_ip(request),
                connection=None
            )

            messages.success(request, '脱敏规则创建成功！')
            return redirect('desensitization:masking_rule_list')
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
        # 从POST数据中获取column_names（JSON字符串）
        column_names_json = request.POST.get('column_names_json', '[]')
        try:
            column_names = json.loads(column_names_json)
        except:
            column_names = []

        # 手动构建数据
        data = {
            'name': request.POST.get('name'),
            'column_names': column_names,
            'masking_type': request.POST.get('masking_type'),
            'masking_params': request.POST.get('masking_params'),
        }

        form = MaskingRuleForm(data, instance=rule)
        if form.is_valid():
            rule = form.save()

            # 添加审计日志
            create_audit_log(
                user=request.user,
                action='update_masking',
                ip_address=get_client_ip(request),
                connection=None
            )

            messages.success(request, '脱敏规则更新成功！')
            return redirect('desensitization:masking_rule_list')
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
            connection=None
        )

        rule.delete()
        messages.success(request, '脱敏规则删除成功！')
        return redirect('desensitization:masking_rule_list')

    return render(request, 'desensitization/delete.html', {'rule': rule})