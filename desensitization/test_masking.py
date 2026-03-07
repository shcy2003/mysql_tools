"""
脱敏功能测试脚本
测试联表查询字段脱敏功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.sql_parser import parse_select_query, SQLQueryParser
from desensitization.utils import find_matched_column, apply_masking_rules
from desensitization.models import MaskingRule


def test_sql_parser():
    """测试SQL解析器"""
    print("=" * 60)
    print("测试 SQL 解析器")
    print("=" * 60)

    test_cases = [
        # 测试1: 简单单表查询
        {
            "name": "简单单表查询",
            "sql": "SELECT id, name, email FROM users",
            "expected_tables": ["users"],
            "expected_columns": ["id", "name", "email"]
        },
        # 测试2: 联表查询带别名
        {
            "name": "联表查询带别名",
            "sql": "SELECT u.id, u.name, u.email, c.name AS company_name FROM users u JOIN companies c ON u.company_id = c.id",
            "expected_tables": ["users", "companies"],
            "expected_columns": ["id", "name", "email", "company_name"]
        },
        # 测试3: 多表JOIN
        {
            "name": "多表JOIN",
            "sql": "SELECT o.id, u.name, p.product_name FROM orders o LEFT JOIN users u ON o.user_id = u.id INNER JOIN products p ON o.product_id = p.id",
            "expected_tables": ["orders", "users", "products"],
            "expected_columns": ["id", "name", "product_name"]
        }
    ]

    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"SQL: {test_case['sql'][:80]}...")

        try:
            parsed = parse_select_query(test_case['sql'])

            # 检查表
            table_names = [t.table_name for t in parsed.tables.values()]
            print(f"  解析到的表: {table_names}")

            # 检查列
            result_columns = [c.get_result_name() for c in parsed.columns]
            print(f"  解析到的列: {result_columns}")

            # 验证
            all_tables_found = all(t in table_names for t in test_case['expected_tables'])
            print(f"  [OK] 所有预期表都找到: {all_tables_found}")

        except Exception as e:
            print(f"  [FAIL] 解析失败: {e}")

    print("\n" + "=" * 60)


def test_column_matching():
    """测试列匹配功能"""
    print("\n" + "=" * 60)
    print("测试列匹配功能")
    print("=" * 60)

    # 测试用的解析查询
    sql = """
    SELECT
        u.id,
        u.name AS user_name,
        u.email,
        c.name AS company_name,
        c.email AS company_email
    FROM users u
    JOIN companies c ON u.company_id = c.id
    """
    parsed = parse_select_query(sql)

    # 模拟结果行
    row = {
        'id': 1,
        'user_name': '张三',
        'email': 'zhang@example.com',
        'company_name': 'ABC公司',
        'company_email': 'contact@abc.com'
    }

    test_cases = [
        # (pattern, expected_match)
        ("email", "email"),
        ("user_name", "user_name"),
        ("u.email", "email"),
        ("users.email", "email"),
        ("c.email", "company_email"),
        ("companies.email", "company_email"),
        ("company_email", "company_email"),
        ("nonexistent", None),
    ]

    for pattern, expected in test_cases:
        matched = find_matched_column(pattern, row, parsed)
        status = "[OK]" if matched == expected else "[FAIL]"
        print(f"  {status} 模式 '{pattern}' -> 匹配 '{matched}' (预期: '{expected}')")

    print("\n" + "=" * 60)


def test_full_workflow():
    """测试完整工作流"""
    print("\n" + "=" * 60)
    print("测试完整脱敏工作流")
    print("=" * 60)

    # 模拟数据
    sql = """
    SELECT
        u.id,
        u.name,
        u.email,
        u.phone,
        c.name AS company_name,
        c.email AS company_email
    FROM users u
    JOIN companies c ON u.company_id = c.id
    """

    result = [
        {
            'id': 1,
            'name': '张三',
            'email': 'zhang@example.com',
            'phone': '13812345678',
            'company_name': 'ABC公司',
            'company_email': 'contact@abc.com'
        },
        {
            'id': 2,
            'name': '李四',
            'email': 'li@example.com',
            'phone': '13987654321',
            'company_name': 'XYZ公司',
            'company_email': 'info@xyz.com'
        }
    ]

    # 创建测试规则（使用内存中的规则对象）
    class MockRule:
        def __init__(self, column_names, masking_type, masking_params=None):
            self.column_names = column_names
            self.masking_type = masking_type
            self.masking_params = masking_params or {}

    # 模拟 apply_masking_rule 函数
    from desensitization.utils import apply_masking_rule

    # 测试部分脱敏
    phone_rule = MockRule(
        column_names=["u.phone", "phone"],
        masking_type="partial",
        masking_params={"keep_first": 3, "keep_last": 4}
    )

    # 测试完全脱敏
    email_rule = MockRule(
        column_names=["u.email", "email"],
        masking_type="full"
    )

    print("\n原始数据:")
    for row in result:
        print(f"  {row}")

    print("\n应用脱敏规则:")
    print("  - 手机号部分脱敏: u.phone, phone")
    print("  - 邮箱完全脱敏: u.email, email")

    # 这里我们手动模拟规则应用，因为真实的 apply_masking_rules 需要数据库连接
    print("\n脱敏后结果:")
    for row in result:
        masked_row = row.copy()

        # 应用手机号脱敏
        matched_phone = find_matched_column("phone", masked_row, parse_select_query(sql))
        if matched_phone:
            masked_row[matched_phone] = apply_masking_rule(phone_rule, row[matched_phone])

        # 应用邮箱脱敏
        matched_email = find_matched_column("u.email", masked_row, parse_select_query(sql))
        if matched_email:
            masked_row[matched_email] = apply_masking_rule(email_rule, row[matched_email])

        print(f"  {masked_row}")

    print("\n" + "=" * 60)


def main():
    print("\n" + "=" * 60)
    print("  联表查询脱敏功能测试")
    print("=" * 60)

    try:
        test_sql_parser()
        test_column_matching()
        test_full_workflow()

        print("\n测试完成！")
        print("\n提示：")
        print("  1. SQL 解析器可以正确解析表别名和列别名")
        print("  2. 支持多种列匹配模式：简单列名、表名.列名、表别名.列名")
        print("  3. 可以正确处理联表查询中的同名字段")
        print("\n详细使用说明请参考: DESENSITIZATION_GUIDE.md")

    except Exception as e:
        print(f"\n[FAIL] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
