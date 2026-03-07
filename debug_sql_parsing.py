#!/usr/bin/env python3
"""
调试SQL解析问题
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.utils import _parse_sql_for_mappings


def test_sql_parsing():
    print("=" * 60)
    print("调试SQL解析问题")
    print("=" * 60)

    # 测试带前导空格的SQL
    sql_with_leading_spaces = """
    SELECT
        u.id AS user_id,
        u.username,
        u.email,
        u.email AS "test",
        l.login_ip,
        l.login_time
    FROM users u
    INNER JOIN user_logs l ON u.id = l.user_id
    """

    print("\n1. 测试带前导空格的SQL:")
    print(f"   前100字符: {repr(sql_with_leading_spaces[:100])}")

    mappings1 = _parse_sql_for_mappings(sql_with_leading_spaces)
    print(f"   解析到的列别名数量: {len(mappings1.get('column_aliases', {}))}")
    for alias, info in mappings1.get('column_aliases', {}).items():
        print(f"   {alias}: {info}")

    # 测试带前导空格但使用strip()的SQL
    sql_stripped = sql_with_leading_spaces.strip()
    print("\n2. 测试使用.strip()的SQL:")
    print(f"   前100字符: {repr(sql_stripped[:100])}")

    mappings2 = _parse_sql_for_mappings(sql_stripped)
    print(f"   解析到的列别名数量: {len(mappings2.get('column_aliases', {}))}")
    for alias, info in mappings2.get('column_aliases', {}).items():
        print(f"   {alias}: {info}")

    # 检查正则表达式
    print("\n3. 检查SELECT正则匹配:")
    select_pattern = r'^SELECT\s+(.+?)\s+FROM\b'
    match1 = re.search(select_pattern, sql_with_leading_spaces, re.IGNORECASE | re.DOTALL)
    print(f"   带前导空格匹配: {match1 is not None}")
    if match1:
        print(f"   匹配内容: {repr(match1.group(1)[:50])}")

    match2 = re.search(select_pattern, sql_stripped, re.IGNORECASE | re.DOTALL)
    print(f"   使用.strip()匹配: {match2 is not None}")
    if match2:
        print(f"   匹配内容: {repr(match2.group(1)[:50])}")

    # 修复: 让正则表达式支持前导空格
    print("\n4. 测试修复后的正则:")
    select_pattern_fixed = r'^\s*SELECT\s+(.+?)\s+FROM\b'
    match3 = re.search(select_pattern_fixed, sql_with_leading_spaces, re.IGNORECASE | re.DOTALL)
    print(f"   带前导空格，用新正则匹配: {match3 is not None}")
    if match3:
        print(f"   匹配内容: {repr(match3.group(1)[:50])}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_sql_parsing()
