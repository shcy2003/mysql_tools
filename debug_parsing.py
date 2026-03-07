"""
调试列别名解析问题
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()


def debug_select_clause_parsing():
    """调试SELECT子句解析"""
    print("=" * 60)
    print("调试SELECT子句解析")
    print("=" * 60)

    sql = """
    SELECT
        u.id AS user_id,
        u.username,
        u.email,
        u.email AS "test",
        l.login_ip,
        l.login_time
    FROM users u
    INNER JOIN user_logs l ON u.id = l.user_id
    """.strip()

    print("原始SQL:")
    print(sql)

    select_pattern = r'^SELECT\s+(.+?)\s+FROM\b'
    select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

    if select_match:
        select_clause = select_match.group(1).strip()
        print(f"\n提取的SELECT子句: '{select_clause}'")

        columns = []
        in_quote = None
        current = []
        comma_count = 0

        # 逐字符解析
        print("\n逐字符解析:")
        for i, char in enumerate(select_clause):
            if char in ['"', "'"]:
                if in_quote == char:
                    in_quote = None
                    print(f"结束引号在位置 {i}: {char}")
                else:
                    in_quote = char
                    print(f"开始引号在位置 {i}: {char}")
            elif char == ',' and not in_quote:
                col_spec = ''.join(current).strip()
                if col_spec:
                    columns.append(col_spec)
                current = []
                comma_count += 1
                print(f"找到第 {comma_count} 列分隔符在位置 {i}")
            else:
                current.append(char)

        if current:
            col_spec = ''.join(current).strip()
            if col_spec:
                columns.append(col_spec)

        print(f"\n共提取到 {len(columns)} 列:")
        for i, col_spec in enumerate(columns):
            print(f"{i+1}: '{col_spec}'")

        print("\n" + "=" * 60)
        return columns
    else:
        print("未找到 SELECT 子句")
        return []


def debug_column_alias_parsing(col_spec):
    """调试列规范解析"""
    print(f"调试 '{col_spec}' 的解析")
    print("-" * 60)

    quoted_alias_pattern = r'^(.*?)\s+(?:AS\s+)?(?:`([^`]+)`|["\']([^"\']+)[\'"])\s*$'
    match = re.search(quoted_alias_pattern, col_spec, re.IGNORECASE)

    if match:
        print("找到带引号的别名模式")
        print("组:", match.groups())
        column_part = match.group(1).strip()
        alias = match.group(2) or match.group(3)
        print(f"列部分: '{column_part}'")
        print(f"别   名: '{alias}'")
        return True

    quoted_column_pattern = r'^`([^`]+)`(?:\.`([^`]+)`)?\s+(?:AS\s+)?(?:`([^`]+)`|["\']([^"\']+)[\'"])\s*$'
    match = re.search(quoted_column_pattern, col_spec, re.IGNORECASE)

    if match:
        print("找到带引号的列和别名模式")
        print("组:", match.groups())
        if match.group(2):
            table_part = match.group(1)
            column_part = match.group(2)
            alias = match.group(3) or match.group(4)
            full_column = f"{table_part}.{column_part}"
        else:
            full_column = match.group(1)
            alias = match.group(3) or match.group(4)
        print(f"列部分: '{full_column}'")
        print(f"别   名: '{alias}'")
        return True

    simple_alias_pattern = r'^(.*?)\s+(?:AS\s+)?([^\s]+)\s*$'
    match = re.search(simple_alias_pattern, col_spec, re.IGNORECASE)

    if match:
        print("找到简单别名模式")
        print("组:", match.groups())
        column_part = match.group(1).strip()
        alias = match.group(2)
        print(f"列部分: '{column_part}'")
        print(f"别   名: '{alias}'")
        return True

    print("未找到匹配的列规范模式")
    return False


def main():
    try:
        columns = debug_select_clause_parsing()
        if columns:
            for i, col_spec in enumerate(columns):
                print(f"\n第 {i+1} 列规范 '{col_spec}':")
                debug_column_alias_parsing(col_spec)
                print()

        print("\n" + "=" * 60)

        # 测试直接调用 _parse_column_aliases
        from desensitization.utils import _parse_column_aliases
        mappings = {}
        _parse_column_aliases(columns, mappings)

        print("解析到的列别名:")
        for alias, info in mappings.items():
            print(f"  {alias}: {info}")

    except Exception as e:
        print(f"调试出错: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
