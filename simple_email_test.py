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
    existing = MaskingRule.objects.filter(
        name="Email字段脱敏-保留首尾",
        column_names=["email"]
    ).first()

    if existing:
        existing.delete()

    rule = MaskingRule.objects.create(
        name="Email字段脱敏-保留首尾",
        column_names=["email"],
        masking_type="regex",
        masking_params={
            "pattern": r'^(\w{2})(.*?)(@.*)$',
            "replacement": r'\1****\3'
        }
    )

    print("Email脱敏规则已创建")
    return rule


def test_email_masking():
    print("=" * 60)
    print("测试Email字段脱敏功能")
    print("=" * 60)

    rule = create_email_masking_rule()

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

    print("原始数据:")
    for item in test_data:
        print(item)

    masked_data = apply_masking_rules(None, "SELECT * FROM users", test_data, None)

    print("\n脱敏后:")
    for item in masked_data:
        print(item)

    print("\n" + "=" * 60)


def demonstrate_rule_configuration():
    print("=" * 60)
    print("Email脱敏规则配置说明")
    print("=" * 60)

    rule_config = {
        "name": "Email字段脱敏",
        "column_names": ["email", "user_email"],
        "masking_type": "regex",
        "masking_params": {
            "pattern": r'^(\w{2})(.*?)(@.*)$',
            "replacement": r'\1****\3'
        }
    }

    print(json.dumps(rule_config, ensure_ascii=False, indent=2))

    print("\n参数说明：")
    print("  pattern: 正则表达式模式")
    print("  replacement: 替换模板")


def main():
    print("MySQL查询平台 - Email字段脱敏演示")
    print("=" * 60)

    try:
        demonstrate_rule_configuration()
        test_email_masking()

        print("\n演示完成！")
        print("说明：")
        print("- 该规则使用正则匹配和分组替换")
        print("- 保留email的前2个字母和@之后的内容")
        print("- 中间内容用 **** 替换")

    except Exception as e:
        print(f"\n演示失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
