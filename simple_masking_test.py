"""
简单的脱敏功能验证脚本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.models import MaskingRule


def create_email_rule():
    """创建email脱敏规则"""
    print("=" * 60)
    print("检查并创建email脱敏规则")
    print("=" * 60)

    rules = MaskingRule.objects.all()
    found = False

    for rule in rules:
        if rule.name == "Email字段脱敏-保留首尾":
            print("找到已存在的规则:", rule.name)
            print("   列名:", rule.column_names)
            print("   类型:", rule.masking_type)
            if rule.masking_type == 'regex' and rule.masking_params:
                print("   模式:", rule.masking_params.get('pattern'))
                print("   替换:", rule.masking_params.get('replacement'))
            found = True
            break

    if not found:
        print("没有找到email脱敏规则，正在创建...")
        rule = MaskingRule.objects.create(
            name="Email字段脱敏-保留首尾",
            column_names=["email", "user_email", "contact_email"],
            masking_type="regex",
            masking_params={
                "pattern": r'^(\w{2})(.*?)(@.*)$',
                "replacement": r'\1****\3'
            }
        )
        print("已创建规则:", rule.name)

    print("\n" + "=" * 60)
    print()
    return found


def test_masking_rule():
    """测试脱敏规则的应用"""
    print("=" * 60)
    print("测试脱敏规则的应用")
    print("=" * 60)

    from desensitization.utils import _apply_single_rule

    test_rule = MaskingRule(
        masking_type="regex",
        masking_params={
            "pattern": r'^(\w{2})(.*?)(@.*)$',
            "replacement": r'\1****\3'
        }
    )

    test_emails = [
        "test1@example.com",
        "test2@test.com",
        "admin@company.co.jp",
        "user.name@site.org"
    ]

    print("原始email:")
    for email in test_emails:
        print("  " + email)

    print("\n脱敏后:")
    results = []
    for email in test_emails:
        masked = _apply_single_rule(test_rule, email)
        results.append(masked)
        print("  " + email + " → " + masked)

    print()
    print("=" * 60)

    return results


def main():
    print("MySQL查询平台 - 脱敏功能验证")
    print()

    rule_found = create_email_rule()

    results = test_masking_rule()

    print()
    print("验证结果:")
    all_valid = True
    for masked in results:
        if '****' in masked and '@' in masked:
            print("格式正确:", masked)
        else:
            print("格式错误:", masked)
            all_valid = False

    print()
    if all_valid:
        print("所有email字段都已正确脱敏!")
    else:
        print("存在脱敏格式问题!")

    print()
    print("说明:")
    print("- 新创建的API已支持脱敏")
    print("- 需要重启服务器来应用修改")
    print("- 访问 http://127.0.0.1:8000/queries/sql/ 测试")


if __name__ == "__main__":
    main()
