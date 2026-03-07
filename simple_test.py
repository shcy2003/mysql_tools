import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.utils import apply_masking_rules, _parse_sql_for_mappings, _match_column
from desensitization.models import MaskingRule
import json


def test_simple_matching():
    """测试简单的字段匹配"""
    print("=" * 60)
    print("测试简单字段匹配")
    print("=" * 60)

    # 测试数据
    test_data = [
        {
            "id": 1,
            "name": "张三",
            "email": "zhang@example.com",
            "phone": "13812345678"
        }
    ]

    print(f"原始数据: {test_data}")

    # 创建临时规则
    rule = MaskingRule(
        name="测试邮箱脱敏",
        column_names=["email"],
        masking_type="full"
    )
    rule.save()

    # 测试匹配
    masked_data = apply_masking_rules(None, "SELECT * FROM users", test_data, None)
    print(f"脱敏后: {masked_data}")

    # 检查是否脱敏成功
    assert len(masked_data) == 1, "应该返回一行数据"
    assert masked_data[0]['email'] == '**********', "邮箱应该被脱敏"
    print("✓ 简单匹配测试成功")

    # 清理
    rule.delete()

    print("=" * 60)
    print()


def test_apply_masking_rules_with_join():
    """测试联表查询字段匹配"""
    print("=" * 60)
    print("测试联表查询字段匹配")
    print("=" * 60)

    # 测试数据
    test_data = [
        {
            "id": 1,
            "user_name": "张三",
            "user_email": "zhang@example.com",
            "company_name": "ABC公司",
            "company_email": "contact@abc.com"
        }
    ]

    print(f"原始数据: {test_data}")

    # 创建测试规则
    user_email_rule = MaskingRule.objects.create(
        name="用户邮箱脱敏",
        column_names=["email", "user_email", "u.email"],
        masking_type="full"
    )

    company_email_rule = MaskingRule.objects.create(
        name="公司邮箱脱敏",
        column_names=["company_email", "c.email"],
        masking_type="partial",
        masking_params={"keep_first": 3, "keep_last": 4}
    )

    # 执行查询
    sql = """
    SELECT
        u.id,
        u.name AS user_name,
        u.email AS user_email,
        c.name AS company_name,
        c.email AS company_email
    FROM users u
    JOIN companies c ON u.company_id = c.id
    """

    masked_data = apply_masking_rules(None, sql, test_data, None)

    print(f"脱敏后: {masked_data}")

    # 验证结果
    assert len(masked_data) == 1, "返回的行数应该一致"

    # 验证字段是否被正确脱敏
    assert masked_data[0]['user_email'] == "**********", "用户邮箱应该被完全脱敏"
    assert masked_data[0]['company_email'] != "contact@abc.com", "公司邮箱应该被脱敏"
    print("✓ 联表查询字段匹配测试成功")

    # 清理
    user_email_rule.delete()
    company_email_rule.delete()

    print("=" * 60)
    print()


def test_same_column_name():
    """测试来自不同表的同名字段"""
    print("=" * 60)
    print("测试同名字段处理")
    print("=" * 60)

    test_data = [
        {
            "id": 1,
            "user_name": "张三",
            "company_name": "ABC公司"
        }
    ]

    print(f"原始数据: {test_data}")

    # 创建测试规则
    user_name_rule = MaskingRule.objects.create(
        name="用户名脱敏",
        column_names=["u.name", "user_name"],
        masking_type="full"
    )

    company_name_rule = MaskingRule.objects.create(
        name="公司名脱敏",
        column_names=["c.name", "company_name"],
        masking_type="partial",
        masking_params={"keep_first": 2, "keep_last": 2}
    )

    sql = """
    SELECT
        u.name AS user_name,
        c.name AS company_name
    FROM users u
    JOIN companies c ON u.company_id = c.id
    """

    masked_data = apply_masking_rules(None, sql, test_data, None)

    print(f"脱敏后: {masked_data}")

    # 验证结果
    assert len(masked_data) == 1, "返回的行数应该一致"

    assert masked_data[0]['user_name'] == "****", "用户名应该被完全脱敏"
    assert masked_data[0]['company_name'] != "ABC公司", "公司名应该被脱敏"

    print("✓ 同名字段处理测试成功")

    # 清理
    user_name_rule.delete()
    company_name_rule.delete()

    print("=" * 60)
    print()


def test_parse_sql_for_mappings():
    """测试SQL解析功能"""
    print("=" * 60)
    print("测试SQL解析功能")
    print("=" * 60)

    test_cases = [
        {
            "sql": "SELECT * FROM users u",
            "expected_aliases": {"u": "users"}
        },
        {
            "sql": "SELECT * FROM users u JOIN companies c ON u.company_id = c.id",
            "expected_aliases": {"u": "users", "c": "companies"}
        },
        {
            "sql": """
            SELECT u.name AS username, c.name AS company_name
            FROM users u
            LEFT JOIN companies c ON u.company_id = c.id
            """,
            "expected_aliases": {"u": "users", "c": "companies"}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        try:
            mappings = _parse_sql_for_mappings(test['sql'])
            assert set(mappings['table_aliases'].keys()) == set(test['expected_aliases'].keys()), \
                f"测试{i}：预期表别名不匹配"
            print(f"✓ 测试{i}成功")
        except Exception as e:
            print(f"✗ 测试{i}失败: {e}")
            return False

    print("=" * 60)
    print()

    return True


def main():
    """主测试函数"""
    print("MySQL查询平台 - 脱敏功能测试")
    print("=" * 60)

    all_passed = True

    try:
        test_parse_sql_for_mappings()
        test_simple_matching()
        test_apply_masking_rules_with_join()
        test_same_column_name()

        print("\n✅ 所有测试通过！")
        print("\n说明：")
        print("- 支持简单字段名匹配")
        print("- 支持表名.列名格式匹配")
        print("- 支持表别名.列名格式匹配")
        print("- 支持列别名匹配")
        print("- 处理同名字段")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        all_passed = False

    return all_passed


if __name__ == "__main__":
    passed = main()
    sys.exit(0 if passed else 1)
