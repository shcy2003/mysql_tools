from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .forms import MaskingRuleForm
from .models import MaskingRule
from audit.utils import create_audit_log
from accounts.views import get_client_ip
import json
import csv
import io
from django.http import HttpResponse


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

        # 处理masking_params
        masking_params = request.POST.get('masking_params')
        if masking_params:
            try:
                masking_params = json.loads(masking_params)
            except:
                pass

        # 手动构建数据
        data = {
            'name': request.POST.get('name'),
            'column_names': column_names,
            'masking_type': request.POST.get('masking_type'),
            'masking_params': masking_params,
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
            # 表单验证失败，显示错误信息
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
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

        # 处理masking_params
        masking_params = request.POST.get('masking_params')
        if masking_params:
            try:
                masking_params = json.loads(masking_params)
            except:
                pass

        # 手动构建数据
        data = {
            'name': request.POST.get('name'),
            'column_names': column_names,
            'masking_type': request.POST.get('masking_type'),
            'masking_params': masking_params,
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
            # 表单验证失败，显示错误信息
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = MaskingRuleForm(instance=rule)

    return render(request, 'desensitization/edit.html', {
        'form': form,
        'rule': rule,
        'initial_column_names': json.dumps(rule.column_names) if rule.column_names else '[]'
    })


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


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_toggle_rule_status(request, rule_id):
    """
    启用/禁用脱敏规则API
    POST /api/desensitization/toggle/<int:rule_id>/

    返回: {"code": 0, "message": "操作成功", "data": {"is_enabled": true/false}}
    """
    try:
        rule = get_object_or_404(MaskingRule, id=rule_id)

        if request.user.role != 'admin':
            return JsonResponse({
                'code': 403,
                'message': '您没有权限执行此操作',
                'data': {}
            })

        # 切换状态
        rule.is_enabled = not rule.is_enabled
        rule.save()

        # 添加审计日志
        action = 'enable_masking' if rule.is_enabled else 'disable_masking'
        create_audit_log(
            user=request.user,
            action=action,
            ip_address=get_client_ip(request),
            connection=None
        )

        return JsonResponse({
            'code': 0,
            'message': f'规则已{"启用" if rule.is_enabled else "禁用"}',
            'data': {'is_enabled': rule.is_enabled}
        })

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'操作失败: {str(e)}',
            'data': {}
        })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_check_column_exists(request):
    """
    检查列名是否已存在于其他脱敏规则中
    POST /api/desensitization/check-column/

    请求体: {"column_name": "phone", "exclude_rule_id": null}
    返回: {"exists": true/false, "rule_name": "规则名称"}
    """
    try:
        data = json.loads(request.body)
        column_name = data.get('column_name')
        exclude_rule_id = data.get('exclude_rule_id')

        if not column_name:
            return JsonResponse({'exists': False, 'error': '列名不能为空'})

        # 查询所有规则
        rules = MaskingRule.objects.all()
        if exclude_rule_id:
            rules = rules.exclude(pk=exclude_rule_id)

        # 检查列名是否存在
        for rule in rules:
            if column_name in rule.column_names:
                return JsonResponse({
                    'exists': True,
                    'rule_name': rule.name
                })

        return JsonResponse({'exists': False})

    except Exception as e:
        return JsonResponse({
            'exists': False,
            'error': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_test_masking_rule(request):
    """
    测试脱敏规则API
    POST /api/desensitization/test-rule/

    支持测试已保存的规则或未保存的临时规则:
    请求体1（已保存规则）: {"rule_id": 1, "test_value": "13812345678"}
    请求体2（临时规则）: {"rule": {"masking_type": "partial", "masking_params": {"keep_first": 3, "keep_last": 4}}, "test_value": "13812345678"}
    返回: {"code": 0, "message": "success", "data": {"original": "13812345678", "masked": "138****5678"}}
    """
    try:
        data = json.loads(request.body)
        test_value = data.get('test_value', '')

        if not test_value:
            return JsonResponse({
                'code': 400,
                'message': '缺少测试值',
                'data': {}
            })

        # 情况1: 测试已保存的规则
        rule_id = data.get('rule_id')
        if rule_id:
            try:
                rule = MaskingRule.objects.get(id=rule_id)
            except MaskingRule.DoesNotExist:
                return JsonResponse({
                    'code': 404,
                    'message': '规则不存在',
                    'data': {}
                })

            from desensitization.utils import _apply_single_rule
            masked_value = _apply_single_rule(rule, test_value)

        else:
            # 情况2: 测试临时规则（未保存到数据库）
            rule_data = data.get('rule')
            if not rule_data or not rule_data.get('masking_type'):
                return JsonResponse({
                    'code': 400,
                    'message': '缺少规则配置',
                    'data': {}
                })

            # 创建临时规则对象
            class TemporaryRule:
                def __init__(self, masking_type, masking_params):
                    self.masking_type = masking_type
                    self.masking_params = masking_params or {}

            temp_rule = TemporaryRule(
                rule_data.get('masking_type'),
                rule_data.get('masking_params')
            )

            from desensitization.utils import _apply_single_rule
            masked_value = _apply_single_rule(temp_rule, test_value)

        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'original': test_value,
                'masked': masked_value
            }
        })

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'测试失败: {str(e)}',
            'data': {}
        })


@login_required
def api_export_masking_rules(request):
    """
    导出脱敏规则API
    GET /api/desensitization/export/
    """
    if request.user.role != 'admin':
        return JsonResponse({
            'code': 403,
            'message': '您没有权限导出脱敏规则',
            'data': {}
        })

    try:
        rules = MaskingRule.objects.all()
        export_data = []

        for rule in rules:
            export_data.append({
                'name': rule.name,
                'is_enabled': rule.is_enabled,
                'column_names': rule.column_names,
                'masking_type': rule.masking_type,
                'masking_params': rule.masking_params,
            })

        # 创建CSV响应
        output = io.StringIO()
        if not export_data:
            # 如果没有数据，只写入表头
            writer = csv.writer(output)
            writer.writerow(['name', 'is_enabled', 'column_names', 'masking_type', 'masking_params'])
        else:
            # 写入表头和数据
            fieldnames = ['name', 'is_enabled', 'column_names', 'masking_type', 'masking_params']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in export_data:
                # 将JSON字段转换为字符串
                row['column_names'] = json.dumps(row['column_names']) if row['column_names'] else '[]'
                row['masking_params'] = json.dumps(row['masking_params']) if row['masking_params'] else '{}'
                writer.writerow(row)

        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="masking_rules.csv"'

        return response

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'导出失败: {str(e)}',
            'data': {}
        })


@login_required
def api_import_masking_rules(request):
    """
    导入脱敏规则API
    POST /api/desensitization/import/
    """
    if request.user.role != 'admin':
        return JsonResponse({
            'code': 403,
            'message': '您没有权限导入脱敏规则',
            'data': {}
        })

    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'code': 400,
                'message': '请上传文件',
                'data': {}
            })

        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return JsonResponse({
                'code': 400,
                'message': '请上传 CSV 格式文件',
                'data': {}
            })

        # 读取CSV文件
        decoded_file = file.read().decode('utf-8-sig')
        input_file = io.StringIO(decoded_file)
        reader = csv.DictReader(input_file)

        imported_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                name = row.get('name', '').strip()
                if not name:
                    skipped_count += 1
                    errors.append(f'第{row_num}行: 规则名称不能为空')
                    continue

                # 解析JSON字段
                column_names = []
                masking_params = {}

                try:
                    column_names = json.loads(row.get('column_names', '[]')) if row.get('column_names') else []
                except:
                    pass

                try:
                    masking_params = json.loads(row.get('masking_params', '{}')) if row.get('masking_params') else {}
                except:
                    pass

                is_enabled = row.get('is_enabled', 'True').strip().lower() == 'true'
                masking_type = row.get('masking_type', 'full').strip()

                # 验证脱敏类型
                valid_types = ['full', 'partial', 'regex']
                if masking_type not in valid_types:
                    masking_type = 'full'

                # 创建规则
                rule = MaskingRule.objects.create(
                    name=name,
                    is_enabled=is_enabled,
                    column_names=column_names,
                    masking_type=masking_type,
                    masking_params=masking_params,
                    created_by=request.user
                )

                imported_count += 1

            except Exception as e:
                skipped_count += 1
                errors.append(f'第{row_num}行: {str(e)}')

        # 添加审计日志
        create_audit_log(
            user=request.user,
            action='import_masking',
            ip_address=get_client_ip(request),
            connection=None
        )

        message = f'导入成功: {imported_count} 条'
        if skipped_count > 0:
            message += f'，跳过: {skipped_count} 条'
        if errors:
            message += f'，错误: {"; ".join(errors[:5])}'
            if len(errors) > 5:
                message += f'... 等{len(errors)}个错误'

        return JsonResponse({
            'code': 0,
            'message': message,
            'data': {
                'imported': imported_count,
                'skipped': skipped_count
            }
        })

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'导入失败: {str(e)}',
            'data': {}
        })