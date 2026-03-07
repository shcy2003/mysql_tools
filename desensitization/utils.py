import re
from typing import Dict, List, Optional, Any
from .models import MaskingRule


def apply_masking_rules(connection, sql, result, user):
    """
    应用脱敏规则到查询结果

    支持的字段匹配模式：
    1. 精确匹配：column_name
    2. 表名.列名：table_name.column_name
    3. 表别名.列名：table_alias.column_name
    4. 列别名：alias_name
    """
    if not result:
        return result

    try:
        # 获取所有全局脱敏规则
        rules = MaskingRule.objects.all()

        if not rules:
            return result

        # 解析SQL中的表别名和列信息
        column_mappings = _parse_sql_for_mappings(sql) if sql else {}

        # 应用脱敏规则到每一行数据
        masked_result = []
        for row in result:
            masked_row = row.copy()

            for rule in rules:
                for column_pattern in rule.column_names:
                    # 找出所有可能匹配的列（一个模式可能匹配多个列别名）
                    matched_columns = _find_all_matched_columns(column_pattern, row, column_mappings)

                    for matched_column in matched_columns:
                        masked_row[matched_column] = _apply_single_rule(
                            rule, row[matched_column])

            masked_result.append(masked_row)

        return masked_result
    except Exception:
        # 如果脱敏过程出错，直接返回原始结果
        return result


def _find_all_matched_columns(pattern: str, row: Dict[str, Any],
                              column_mappings: Dict[str, Any]) -> list:
    """
    找出所有匹配模式的列（一个模式可能匹配多个列别名）

    返回匹配的列名列表
    """
    matched = []
    column_aliases = column_mappings.get('column_aliases', {})
    table_aliases = column_mappings.get('table_aliases', {})

    # 1. 直接精确匹配
    if pattern in row and pattern not in matched:
        matched.append(pattern)

    # 2. 通过列别名匹配
    for result_col in row.keys():
        result_col_lower = result_col.lower()

        if result_col_lower in column_aliases:
            alias_info = column_aliases[result_col_lower]
            table_alias, original_col = alias_info

            # 检查原始列是否匹配模式
            if original_col.lower() == pattern.lower():
                if result_col not in matched:
                    matched.append(result_col)

            # 检查表.列格式
            if '.' in pattern:
                pattern_parts = pattern.split('.', 1)
                table_part, col_part = pattern_parts

                if original_col.lower() == col_part.lower():
                    if not table_part or (table_alias and table_alias == table_part):
                        if result_col not in matched:
                            matched.append(result_col)
                    elif table_aliases and (
                            (table_alias and table_aliases.get(table_alias) == table_part) or
                            table_part in table_aliases.values()
                    ):
                        if result_col not in matched:
                            matched.append(result_col)

    # 3. 不区分大小写的直接匹配
    for result_col in row.keys():
        if result_col.lower() == pattern.lower() and result_col not in matched:
            matched.append(result_col)

    return matched


def _parse_sql_for_mappings(sql: str) -> Dict[str, Dict[str, str]]:
    """
    简单解析SQL，提取表别名和列信息

    返回: {
        'table_aliases': {alias: table_name},
        'column_aliases': {alias: (table_alias, column_name)}
    }
    """
    mappings = {
        'table_aliases': {},
        'column_aliases': {}
    }

    if not sql:
        return mappings

    sql_upper = sql.upper()

    # 1. 提取表别名：FROM table [AS] alias
    from_pattern = r'\bFROM\b\s+([^;]+?)(?:\s+(?:WHERE|GROUP|ORDER|HAVING|LIMIT|$))'
    from_match = re.search(from_pattern, sql, re.IGNORECASE)

    if from_match:
        from_clause = from_match.group(1)
        _parse_table_aliases_from_clause(from_clause, mappings['table_aliases'])

    # 2. 提取JOIN表别名
    join_patterns = [
        r'\b(?:INNER\s+)?JOIN\b\s+([^;]+?)(?:\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|$))',
        r'\bLEFT\s+(?:OUTER\s+)?JOIN\b\s+([^;]+?)(?:\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|$))',
        r'\bRIGHT\s+(?:OUTER\s+)?JOIN\b\s+([^;]+?)(?:\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|$))',
    ]

    for pattern in join_patterns:
        matches = re.finditer(pattern, sql, re.IGNORECASE)
        for match in matches:
            join_clause = match.group(1)
            _parse_table_aliases_from_clause(join_clause, mappings['table_aliases'])

    # 3. 提取列别名：SELECT column AS alias
    _parse_column_aliases(sql, mappings['column_aliases'])

    return mappings


def _parse_column_aliases(sql: str, column_aliases: Dict[str, tuple]):
    """从SELECT子句中解析列别名"""
    # 提取 SELECT 和 FROM 之间的内容（允许SELECT前有空白字符）
    select_pattern = r'^\s*SELECT\s+(.+?)\s+FROM\b'
    select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

    if not select_match:
        return

    select_clause = select_match.group(1).strip()

    # 移除 DISTINCT 等关键字
    select_clause = re.sub(r'^\s*(?:DISTINCT|ALL)\s+', '', select_clause, flags=re.IGNORECASE)

    # 分割列列表（考虑函数、括号、引号）
    columns = _split_columns_by_comma(select_clause)

    for col_spec in columns:
        col_spec = col_spec.strip()
        if col_spec == '*':
            continue

        # 解析列规范
        _parse_single_column_alias(col_spec, column_aliases)


def _split_columns_by_comma(text: str) -> list:
    """按逗号分割SELECT列列表，考虑括号和引号"""
    result = []
    current = []
    in_quote = None
    paren_depth = 0
    i = 0

    while i < len(text):
        char = text[i]

        if char in ['`', '"', "'"]:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
            current.append(char)
        elif char == '(' and in_quote is None:
            paren_depth += 1
            current.append(char)
        elif char == ')' and in_quote is None:
            paren_depth -= 1
            current.append(char)
        elif char == ',' and in_quote is None and paren_depth == 0:
            result.append(''.join(current))
            current = []
        else:
            current.append(char)

        i += 1

    if current:
        result.append(''.join(current))

    return result


def _parse_single_column_alias(col_spec: str, column_aliases: Dict[str, tuple]):
    """解析单个列规范，提取别名信息"""
    # 匹配模式：[table.]column [AS] alias
    # 支持：u.email, u.email as test, `u`.`email` AS `test`, u.email AS "test"

    # 先处理单引号和双引号内的别名
    quoted_alias_pattern = r'^(.*?)\s+(?:AS\s+)?(?:`([^`]+)`|["\']([^"\']+)[\'"])\s*$'
    match = re.search(quoted_alias_pattern, col_spec, re.IGNORECASE)

    if match:
        column_part = match.group(1).strip()
        alias = match.group(2) or match.group(3)  # 取有值的那个组
        _add_column_alias(column_part, alias, column_aliases)
        return

    # 再处理引号内的表和列
    quoted_column_pattern = r'^`([^`]+)`(?:\.`([^`]+)`)?\s+(?:AS\s+)?(?:`([^`]+)`|["\']([^"\']+)[\'"])\s*$'
    match = re.search(quoted_column_pattern, col_spec, re.IGNORECASE)

    if match:
        if match.group(2):
            table_part = match.group(1)
            column_part = match.group(2)
            alias = match.group(3) or match.group(4)
            full_column = f"{table_part}.{column_part}"
        else:
            full_column = match.group(1)
            alias = match.group(3) or match.group(4)
        _add_column_alias(full_column, alias, column_aliases)
        return

    # 处理不带引号的别名
    simple_alias_pattern = r'^(.*?)\s+(?:AS\s+)?([^\s]+)\s*$'
    match = re.search(simple_alias_pattern, col_spec, re.IGNORECASE)

    if match:
        column_part = match.group(1).strip()
        alias = match.group(2)
        _add_column_alias(column_part, alias, column_aliases)
        return


def _add_column_alias(column_part: str, alias: str, column_aliases: Dict[str, tuple]):
    """添加列别名到映射中"""
    # 解析列部分，提取表别名和列名
    table_alias = None
    column_name = column_part

    if '.' in column_part:
        parts = column_part.split('.', 1)
        table_alias = parts[0].strip()
        column_name = parts[1].strip()

    # 移除可能的引号
    table_alias = table_alias.strip('`') if table_alias else None
    column_name = column_name.strip('`')

    column_aliases[alias.lower()] = (table_alias, column_name)


def _parse_table_aliases_from_clause(clause: str, table_aliases: Dict[str, str]):
    """从FROM/JOIN子句中解析表别名"""
    # 移除任何括号内容
    clause = re.sub(r'\([^)]*\)', '', clause)

    # 分割多个表
    tables = re.split(r'\s*,\s*', clause.strip())

    for table_spec in tables:
        table_spec = table_spec.strip()
        if not table_spec:
            continue

        # 匹配: table [AS] alias
        match = re.match(r'^(?:`?([^`.\s]+)`?\.)?`?([^`.\s]+)`?(?:\s+(?:AS\s+)?`?([^`\s]+)`?)?$', table_spec, re.IGNORECASE)
        if match:
            _, table_name, alias = match.groups()
            if alias:
                table_aliases[alias.lower()] = table_name
            else:
                table_aliases[table_name.lower()] = table_name


def _match_column(pattern: str, row: Dict[str, Any],
                 column_mappings: Dict[str, Any]) -> Optional[str]:
    """
    根据模式查找匹配的列名

    支持的模式:
    - 'email' -> 直接匹配
    - 'u.email' -> 表别名.列名
    - 'users.email' -> 表名.列名
    - 列别名 -> 支持别名匹配
    """
    # 获取别名映射
    column_aliases = column_mappings.get('column_aliases', {})
    table_aliases = column_mappings.get('table_aliases', {})

    # 模式1: 直接精确匹配（包括列别名）
    if pattern in row:
        return pattern

    # 检查是否有结果列与模式匹配（不区分大小写）
    for result_col in row.keys():
        if result_col.lower() == pattern.lower():
            return result_col

    # 模式2: 通过列别名匹配（重点修复这里）
    for result_col in row.keys():
        result_col_lower = result_col.lower()

        # 检查结果列是否是某个列的别名
        if result_col_lower in column_aliases:
            alias_info = column_aliases[result_col_lower]
            table_alias, original_col = alias_info

            # 检查原始列是否匹配模式
            if original_col.lower() == pattern.lower():
                return result_col

            if '.' in pattern:
                pattern_parts = pattern.split('.', 1)
                table_part, col_part = pattern_parts

                if original_col.lower() == col_part.lower():
                    # 检查表部分是否匹配
                    if not table_part or (table_alias and table_alias == table_part):
                        return result_col
                    elif table_aliases and (
                            (table_alias and table_aliases.get(table_alias) == table_part) or
                            (table_part in table_aliases.values())
                    ):
                        return result_col

    # 模式3: 包含点号，可能是表.列格式（尝试原始列名）
    if '.' in pattern:
        parts = pattern.split('.', 1)
        table_part = parts[0].lower()
        column_part = parts[1]

        # 查找结果列中可能匹配的列
        for result_col in row.keys():
            result_col_lower = result_col.lower()

            # 检查结果列是否有对应的原始列名
            if result_col_lower in column_aliases:
                alias_info = column_aliases[result_col_lower]
                alias_table, original_col = alias_info

                if original_col.lower() == column_part.lower():
                    if not table_part:
                        return result_col

                    # 检查表别名或表名是否匹配
                    if alias_table and (alias_table == table_part):
                        return result_col

                    if table_aliases and (
                            (alias_table and table_aliases.get(alias_table) == table_part) or
                            table_part in table_aliases.values()
                    ):
                        return result_col

            # 简单匹配原始结果列名
            if result_col_lower == column_part.lower():
                return result_col

    # 模式4: 简单列名匹配（最后尝试）
    for result_col in row.keys():
        if result_col.lower() == pattern.lower():
            return result_col

    return None


def _apply_single_rule(rule, value):
    """应用单个脱敏规则到值"""
    if value is None:
        return None

    value_str = str(value)

    if rule.masking_type == 'full':
        return '*' * len(value_str)
    elif rule.masking_type == 'partial':
        params = rule.masking_params or {}
        keep_first = params.get('keep_first', 0)
        keep_last = params.get('keep_last', 0)

        if keep_first + keep_last >= len(value_str):
            return value_str

        mask_length = len(value_str) - keep_first - keep_last
        result = value_str[:keep_first] + '*' * mask_length
        if keep_last > 0:
            result += value_str[-keep_last:]
        return result
    elif rule.masking_type == 'regex':
        params = rule.masking_params or {}
        pattern = params.get('pattern', '')
        replacement = params.get('replacement', '')

        try:
            regex = re.compile(pattern)

            if replacement:
                # 使用自定义替换
                return regex.sub(replacement, value_str)
            else:
                # 默认替换：用*替换匹配的内容
                return regex.sub('*', value_str)
        except:
            return '*' * len(value_str)
    else:
        return value_str


def apply_masking_rule(rule, value):
    """保留旧函数名的兼容性"""
    return _apply_single_rule(rule, value)
