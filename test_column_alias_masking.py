"""
测试列别名脱敏功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.utils import apply_masking_rules, _parse_sql_for_mappings
from desensitization.models import MaskingRule


def test_column_alias_parsing():
    print("=" * 60)
    print("测试列别名解析功能")
    print("=" * 60)

    # 测试SQL
    test_sqls = [
        "SELECT u.id AS user_id, u.username, u.email AS test, l.login_ip FROM users u JOIN user_logs l ON u.id = l.user_id",
        "SELECT email AS customer_email, u.name FROM users u",
        "SELECT `email` AS `user_email` FROM users",
    ]

    for i, sql in enumerate(test_sqls, 1):
        print(f"\nSQL {i}:")
        print(sql)

        mappings = _parse_sql_for_mappings(sql)

        print("\n解析结果:")
        print(f"  表别名: {mappings.get('table_aliases', {})}")
        print(f"  列别名: {mappings.get('column_aliases', {})}")

    print("\n" + "=" * 60)


def test_masking_with_alias():
    print("\n" + "=" * 60)
    print("测试使用列别名的脱敏")
    print("=" * 60)

    from desensitization.utils import _apply_single_rule

    # 创建测试规则
    test_rule = MaskingRule(
        masking_type="regex",
        masking_params={
            "pattern": r'^(\w{2})(.*?)(@.*)$',
            "replacement": r'\1****\3'
        }
    )

    # 测试数据
    test_data = [
        {
            "user_id": 1,
            "username": "User_1",
            "email": "test1@example.com",
            "test": "test1@example.com",
            "login_ip": "192.168.1.1"
        }
    ]

    sql = "SELECT u.id AS user_id, u.email AS test FROM users u"

    mappings = _parse_sql_for_mappings(sql)
    print("SQL:", sql)
    print("解析到的列别名:", mappings.get('column_aliases', {}))

    # 手动测试脱敏规则应用
    print("\n测试数据:")
    for item in test_data:
        print(item)

    print("\n测试脱敏:")
    # 创建临时规则对象
    from desensitization.utils import _match_column

    # 模拟匹配过程
    for result_col in test_data[0].keys():
        # 尝试用 'email' 模式匹配
        matched = _match_column('email', test_data[0], mappings)
        if matched:
            print(f"  用 'email' 模式匹配到: {matched}")
            original_val = test_data[0][matched]
            masked_val = _apply_single_rule(test_rule, original_val)
            print(f"    原始: {original_val}")
            print(f"    脱敏: {masked_val}")

    print("\n" + "=" * 60)


def test_full_workflow():
    print("\n" + "=" * 60)
    print("测试完整工作流")
    print("=" * 60)

    # 确保有规则
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

    # 测试数据
    test_data = [
        {
            "user_id": 1,
            "username": "User_1",
            "email": "test1@example.com",
            "test": "test1@example.com",
            "login_ip": "192.168.1.1"
        },
        {
            "user_id": 2,
            "username": "User_2",
            "email": "test2@test.com",
            "test": "test2@test.com",
            "login_ip": "192.168.1.2"
        }
    ]

    sql = "SELECT u.id AS user_id, u.email AS test FROM users u"

    print("SQL:", sql)
    print("\n原始数据:")
    for item in test_data:
        print(item)

    # 应用脱敏
    masked_result = apply_masking_rules(None, sql, test_data, None)

    print("\n脱敏后:")
    for item in masked_result:
        print(item)

    print("\n验证结果:")
    all_valid = True
    for original, masked in zip(test_data, masked_result):
        if masked.get("test") and masked["test"] != original.get("test") and "****" in masked["test"]:
            print(f"  OK: test字段已被脱敏 - {original.get('test')} -> {masked.get('test')}")
        else:
            print(f"  FAIL: test字段未被正确脱敏 - {original.get('test')} -> {masked.get('test')}")
            all_valid = False

    print(f"\n整体结果: {'OK' if all_valid else 'FAIL'}")
    print("\n" + "=" * 60)


def main():
    print("MySQL查询平台 - 列别名脱敏测试")

    try:
        test_column_alias_parsing()
        test_masking_with_alias()
        test_full_workflow()

        print("\n测试完成")
        print("\n说明:")
        print("- 现在即使使用AS别名，email字段也能正确脱敏")
        print("- 规则中配置 'email'，也会匹配到别名为'test'的email列")

    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
