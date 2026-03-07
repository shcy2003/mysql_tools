"""
简单的列别名测试（无emoji，避免编码问题）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.utils import apply_masking_rules, _parse_sql_for_mappings
from desensitization.models import MaskingRule


def test_quoted_alias_parsing():
    print("=" * 60)
    print("测试带引号的列别名解析")
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
    """

    mappings = _parse_sql_for_mappings(sql)

    print("SQL:")
    print(sql.strip())

    print("\n解析到的列别名:")
    for alias, info in mappings.get('column_aliases', {}).items():
        print(f"  {alias}: {info}")

    print("\n" + "=" * 60)


def test_masking():
    print("\n" + "=" * 60)
    print("测试使用列别名的脱敏")
    print("=" * 60)

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

    print("规则名:", rule.name)
    print("列名列表:", rule.column_names)

    # 测试数据
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

    print("原始数据:")
    for row in test_data:
        print(row)

    masked_result = apply_masking_rules(None, sql, test_data, None)

    print("脱敏后数据:")
    for row in masked_result:
        print(row)

    print("\n" + "=" * 60)
    print("验证:")
    all_ok = True

    for i, (orig, masked) in enumerate(zip(test_data, masked_result)):
        print(f"第 {i+1} 行:")

        if masked['email'] == orig['email']:
            print(f"  [FAIL] email字段未脱敏: {orig['email']}")
            all_ok = False
        else:
            print(f"  [OK] email字段已脱敏: {orig['email']} -> {masked['email']}")

        if masked['test'] == orig['test']:
            print(f"  [FAIL] test字段未脱敏: {orig['test']}")
            all_ok = False
        else:
            print(f"  [OK] test字段已脱敏: {orig['test']} -> {masked['test']}")

    if all_ok:
        print("\n[OK] 所有字段都已正确脱敏!")
        print("现在即使使用 AS 'test' 或 AS \"test\" 这样的带引号别名, email字段也能正确匹配")
    else:
        print("\n[FAIL] 存在字段未被正确脱敏!")


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
    """


def main():
    try:
        test_quoted_alias_parsing()
        test_masking()

        print("\n" + "=" * 60)
        print("测试完成")

    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
