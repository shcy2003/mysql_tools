import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.models import MaskingRule
from desensitization.utils import apply_masking_rules
import json


def create_email_masking_rule():
    """创建email脱敏规则"""
    # 检查是否已存在相同规则
    existing = MaskingRule.objects.filter(
        name="Email字段脱敏-保留首尾",
        column_names=["email"]
    ).first()

    if existing:
        existing.delete()

    rule = MaskingRule.objects.create(
        name="Email字段脱敏-保留首尾",
        column_names=["email"],  # 支持多个列名，例如 ["email", "user_email"]
        masking_type="regex",
        masking_params={
            "pattern": r'^(\w{2})(.*?)(@.*)$',
            "replacement": r'\1****\3'
        }
    )

    print("✅ Email脱敏规则已创建")
    return rule


def test_email_masking():
    """测试email脱敏"""
    print("=" * 60)
    print("测试Email字段脱敏功能")
    print("=" * 60)

    # 创建规则
    rule = create_email_masking_rule()

    # 测试数据
    test_data = [
        {
            "id": 1,
            "name": "张三",
            "email": "zhangsan@example.com"
        },
        {
            "id": 2,
            "name": "李四",
            "email": "lisi_abc@test.com.cn"
        },
        {
            "id": 3,
            "name": "王五",
            "email": "wang.wu@company.co.jp"
        }
    ]

    print(f"原始数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")

    # 执行脱敏
    masked_data = apply_masking_rules(None, "SELECT * FROM users", test_data, None)

    print(f"脱敏后: {json.dumps(masked_data, ensure_ascii=False, indent=2)}")

    # 验证结果
    for i, item in enumerate(masked_data):
        original = test_data[i]['email']
        masked = item['email']

        print(f"\n第{i+1}条验证:")
        print(f"  原始: {original}")
        print(f"  脱敏后: {masked}")

        # 检查是否保留了前2个字符和@之后的内容
        assert masked.startswith(original[:2]), "应该保留前2个字符"
        assert masked.endswith(original[original.find('@'):]), "应该保留@之后的内容"
        assert '****' in masked, "中间应该有****占位"
        print(f"  ✅ 验证成功")

    print("\n" + "=" * 60)
    print()


def demonstrate_rule_configuration():
    """展示规则配置方式"""
    print("=" * 60)
    print("Email脱敏规则配置说明")
    print("=" * 60)

    rule_config = {
        "name": "Email字段脱敏",
        "column_names": ["email", "user_email", "contact_email"],  # 支持多个列
        "masking_type": "regex",
        "masking_params": {
            "pattern": r'^(\w{2})(.*?)(@.*)$',
            "replacement": r'\1****\3'
        }
    }

    print("规则配置内容：")
    print(json.dumps(rule_config, ensure_ascii=False, indent=2))

    print("\n参数说明：")
    print("  - pattern: 正则表达式模式")
    print("    - ^(\\w{2}) : 匹配前2个字母数字字符")
    print("    - (.*?) : 匹配中间任意字符（非贪婪模式）")
    print("    - (@.*)$ : 匹配@及之后的所有内容")
    print()
    print("  - replacement: 替换模板")
    print("    - \\1 : 引用第一个分组（前2个字符）")
    print("    - **** : 固定的星号占位")
    print("    - \\3 : 引用第三个分组（@之后的内容）")

    print()
    print("=" * 60)
    print()


def verify_regex_functionality():
    """直接验证正则匹配功能"""
    print("=" * 60)
    print("直接验证正则匹配功能")
    print("=" * 60)

    import re

    pattern = r'^(\w{2})(.*?)(@.*)$'
    replacement = r'\1****\3'

    test_cases = [
        ("zhangsan@example.com", "zh****@example.com"),
        ("lisi_abc@test.com.cn", "li****@test.com.cn"),
        ("wang.wu@company.co.jp", "wa****@company.co.jp"),
        ("a@b.c", "a****@b.c"),
        ("ab@cd", "ab****@cd")
    ]

    all_passed = True
    for original, expected in test_cases:
        try:
            result = re.sub(pattern, replacement, original)
            assert result == expected, f"{original} 应该被替换成 {expected}"
            print(f"✅ {original} -> {result}")
        except Exception as e:
            print(f"❌ {original} 失败: {e}")
            all_passed = False

    if all_passed:
        print("\n✅ 所有正则匹配测试通过！")
    else:
        print("\n❌ 部分测试失败！")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("MySQL查询平台 - Email字段脱敏演示")
    print("=" * 60)

    try:
        verify_regex_functionality()
        demonstrate_rule_configuration()
        test_email_masking()

        print("\n🎉 演示完成！")
        print("\n说明：")
        print("- 该规则使用正则匹配和分组替换")
        print("- 保留email的前2个字母和@之后的所有内容")
        print("- 中间内容用 **** 替换")
        print("- 支持多种email格式（包括带下划线、点号等）")
        print("\n规则已保存到数据库，可以在后台管理中查看和编辑")

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
