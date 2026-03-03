import re
from .models import MaskingRule


def apply_masking_rules(connection, sql, result, user):
    """应用脱敏规则到查询结果"""
    if not result:
        return result

    # 获取该连接的所有脱敏规则
    rules = MaskingRule.objects.filter(connection=connection)

    if not rules:
        return result

    # 应用脱敏规则到每一行数据
    masked_result = []
    for row in result:
        masked_row = row.copy()

        for rule in rules:
            if rule.column_name in masked_row:
                masked_row[rule.column_name] = apply_masking_rule(
                    rule, row[rule.column_name])

        masked_result.append(masked_row)

    return masked_result


def apply_masking_rule(rule, value):
    """根据脱敏规则脱敏值"""
    if value is None:
        return None

    value_str = str(value)

    if rule.masking_type == 'full':
        return apply_full_masking(value_str)
    elif rule.masking_type == 'partial':
        return apply_partial_masking(value_str, rule.masking_params)
    elif rule.masking_type == 'regex':
        return apply_regex_masking(value_str, rule.masking_params)
    else:
        return value


def apply_full_masking(value):
    """完全脱敏：替换为相同长度的星号"""
    return '*' * len(value)


def apply_partial_masking(value, params):
    """部分脱敏：保留前 N 个字符和后 M 个字符，中间替换为星号"""
    if not params:
        return apply_full_masking(value)

    keep_first = params.get('keep_first', 0)
    keep_last = params.get('keep_last', 0)

    if keep_first + keep_last >= len(value):
        return value

    mask_length = len(value) - keep_first - keep_last
    return value[:keep_first] + '*' * mask_length + value[-keep_last:]


def apply_regex_masking(value, params):
    """正则匹配替换：匹配到的内容替换为星号"""
    if not params or 'pattern' not in params:
        return apply_full_masking(value)

    pattern = params['pattern']
    try:
        regex = re.compile(pattern)
        return regex.sub('*', value)
    except:
        return apply_full_masking(value)


def get_column_masking_rule(connection, table_name, column_name):
    """获取指定列的脱敏规则"""
    try:
        return MaskingRule.objects.get(
            connection=connection,
            table_name=table_name,
            column_name=column_name
        )
    except MaskingRule.DoesNotExist:
        return None