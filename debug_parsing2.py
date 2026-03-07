"""
调试 _parse_sql_for_mappings 函数
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()


def debug_parse_sql_for_mappings():
    print("=" * 60)
    print("调试 _parse_sql_for_mappings 函数")
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

    from desensitization.utils import _parse_sql_for_mappings
    mappings = _parse_sql_for_mappings(sql)

    print(f"\n解析到的列别名:")
    for alias, info in mappings.get('column_aliases', {}).items():
        print(f"  {alias}: {info}")

    if "test" in mappings.get('column_aliases', {}):
        print("\n✅ 成功解析到列别名'test'")
        table_alias, col_name = mappings.get('column_aliases', {})["test"]
        print(f"  对应原始列: {table_alias}.{col_name}")
    else:
        print("\n❌ 未能解析到列别名'test'")

    print("\n" + "=" * 60)


def test_masking():
    print("\n" + "=" * 60)
    print("测试使用列别名的脱敏")
    print("=" * 60)

    from desensitization.utils import _parse_sql_for_mappings, apply_masking_rules
    from desensitization.models import MaskingRule

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

    # 创建测试数据
    test_data = [
        {
            "user_id": 1,
            "username": "User_1",
            "email": "test1@example.com",
            "test": "test1@example.com",
            "login_ip": "192.168.1.1",
            "login_time": "2026-03-07T08:00:55"
        },
        {
            "user_id": 2,
            "username": "User_2",
            "email": "test2@example.com",
            "test": "test2@example.com",
            "login_ip": "192.168.1.2",
            "login_time": "2026-03-07T08:00:55"
        }
    ]

    rule = MaskingRule.objects.filter(name="Email字段脱敏-保留首尾").first()
    if not rule:
        rule = MaskingRule.objects.create(
            name="Email字段脱敏-保留首尾",
            column_names=["email"],
            masking_type="regex",
            masking_params={
                "pattern": r'^(\w{2})(.*?)(@.*)$',
                "replacement": r'\1****\3'
            }
        )

    masked_result = apply_masking_rules(None, sql, test_data, None)

    for i, (original, masked) in enumerate(zip(test_data, masked_result)):
        print(f"第 {i+1} 行:")
        print(f"  email: {original['email']} -> {masked['email']}")
        print(f"  test: {original['test']} -> {masked['test']}")


def test_match_column():
    print("\n" + "=" * 60)
    print("测试 _find_all_matched_columns 函数")
    print("=" * 60)

    from desensitization.utils import _parse_sql_for_mappings, _find_all_matched_columns

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

    test_data = [
        {
            "user_id": 1,
            "username": "User_1",
            "email": "test1@example.com",
            "test": "test1@example.com",
            "login_ip": "192.168.1.1",
            "login_time": "2026-03-07T08:00:55"
        }
    ]

    row = test_data[0]

    mappings = _parse_sql_for_mappings(sql)

    matched_columns = _find_all_matched_columns("email", row, mappings)

    print(f"查找模式 'email' 匹配到的列:")
    for col in matched_columns:
        print(f"  '{col}': 值 '{row[col]}'")


def main():
    print("MySQL查询平台 - 列别名解析调试")

    try:
        debug_parse_sql_for_mappings()
        test_match_column()
        test_masking()

    except Exception as e:
        print(f"\n调试出错: {e}")
        import traceback
        print(traceback.format_exc())

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
