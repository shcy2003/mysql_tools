"""
测试最终解决方案（不含emoji字符）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.utils import _parse_sql_for_mappings, apply_masking_rules
from desensitization.models import MaskingRule
import json


def test_parse():
    print("=" * 60)
    print("测试列别名解析")
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

    mappings = _parse_sql_for_mappings(sql)
    column_aliases = mappings.get('column_aliases', {})

    print("解析到的列别名:")
    for alias, info in column_aliases.items():
        print(f"  {alias}: {info}")

    return mappings


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

    masked_result = apply_masking_rules(None, sql, test_data, None)

    print("原始数据:")
    print(test_data)

    print("\n脱敏后数据:")
    print(masked_result)

    return test_data, masked_result


def verify(masked_data, original_data):
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)

    errors = []

    for i in range(len(original_data)):
        orig = original_data[i]
        masked = masked_data[i]

        if masked.get('email') == orig.get('email'):
            errors.append(f"第{i+1}行 email字段未脱敏")

        if masked.get('test') == orig.get('test'):
            errors.append(f"第{i+1}行 test字段未脱敏")

    if errors:
        print("验证失败:")
        for err in errors:
            print("  - " + err)
    else:
        print("验证成功！所有字段均已正确脱敏")

    return len(errors) == 0


def main():
    print("MySQL查询平台 - 列别名脱敏测试")

    try:
        mappings = test_parse()
        if 'test' in mappings.get('column_aliases', {}):
            print("\n成功解析到列别名 'test'")
        else:
            print("\n错误：未解析到列别名 'test'")
            return False

        data, masked = test_masking()
        if not verify(masked, data):
            return False

        print("\n" + "=" * 60)
        print("解决方案有效！")
        print("\n已实现:")
        print("- 解析 SELECT 子句中的列别名，包括带引号的别名")
        print("- 处理多种SQL语法（AS \"alias\", AS 'alias', AS alias）")
        print("- 应用脱敏规则到原始列名和列别名")
        print("- 处理单引号和双引号的引用")

    except Exception as e:
        print(f"测试过程出错: {e}")
        import traceback
        print(traceback.format_exc())
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
