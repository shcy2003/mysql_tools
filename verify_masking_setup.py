"""
验证脱敏规则设置
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.models import MaskingRule
from desensitization.utils import apply_masking_rules


def check_and_create_rule():
    print("=" * 60)
    print("检查脱敏规则")
    print("=" * 60)

    # 检查是否有email脱敏规则
    rules = MaskingRule.objects.filter(column_names__contains=["email"])

    if rules.exists():
        print(f"✅ 找到 {rules.count()} 个包含email的脱敏规则")
        for rule in rules:
            print(f"  - {rule.name}: {rule.column_names} ({rule.masking_type})")
            if rule.masking_type == 'regex' and rule.masking_params:
                print(f"    模式: {rule.masking_params.get('pattern')}")
                print(f"    替换: {rule.masking_params.get('replacement')}")
    else:
        print("❌ 没有找到email脱敏规则，正在创建...")

        rule = MaskingRule.objects.create(
            name="Email字段脱敏-保留首尾",
            column_names=["email", "user_email", "contact_email"],
            masking_type="regex",
            masking_params={
                "pattern": r'^(\w{2})(.*?)(@.*)$',
                "replacement": r'\1****\3'
            }
        )

        print(f"✅ 已创建规则: {rule.name}")
        print(f"   列名: {rule.column_names}")
        print(f"   类型: {rule.masking_type}")

    print("\n" + "=" * 60)
    print()


def test_masking_logic():
    print("=" * 60)
    print("测试脱敏逻辑")
    print("=" * 60)

    # 测试数据
    test_data = [
        {"id": 1, "username": "user1", "email": "test1@example.com"},
        {"id": 2, "username": "user2", "email": "test2@test.com"},
        {"id": 3, "username": "user3", "email": "admin@company.co.jp"},
    ]

    print(f"原始数据: {test_data}")

    # 获取规则
    rules = MaskingRule.objects.filter(column_names__contains=["email"])
    if not rules:
        print("❌ 没有找到email规则")
        return

    # 模拟脱敏
    from desensitization.utils import _apply_single_rule

    rule = rules.first()
    print(f"\n使用规则: {rule.name}")

    masked_data = []
    for item in test_data:
        masked_item = item.copy()
        if "email" in masked_item:
            masked_item["email"] = _apply_single_rule(rule, masked_item["email"])
        masked_data.append(masked_item)

    print(f"\n脱敏后数据: {masked_data}")

    # 验证结果
    print("\n验证结果:")
    all_correct = True
    for original, masked in zip(test_data, masked_data):
        orig_email = original["email"]
        mask_email = masked["email"]

        expected_start = orig_email[:2]
        expected_end = orig_email[orig_email.find('@'):]

        print(f"  原始: {orig_email}")
        print(f"  脱敏: {mask_email}")

        if mask_email.startswith(expected_start) and mask_email.endswith(expected_end) and "****" in mask_email:
            print(f"  ✅ 正确")
        else:
            print(f"  ❌ 错误")
            all_correct = False

    print()
    print("=" * 60)

    return all_correct


def main():
    print("MySQL查询平台 - 脱敏功能验证")
    print()

    check_and_create_rule()
    test_masking_logic()

    print("\n说明:")
    print("- 脱敏规则已添加到API查询函数中")
    print("- API执行查询时会自动应用脱敏")
    print("- 导出Excel时也会自动应用脱敏")
    print("- 可以在后台管理界面中管理脱敏规则")


if __name__ == "__main__":
    main()
