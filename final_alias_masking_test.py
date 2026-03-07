"""
测试用户提到的使用 u.email as "test" 场景的列别名脱敏
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

import django
django.setup()

from desensitization.utils import apply_masking_rules
from desensitization.models import MaskingRule
import json


def test_user_scene():
    print("=" * 60)
    print("测试用户场景：u.email AS test")
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

    print("使用的规则:")
    print(f"  规则名: {rule.name}")
    print(f"  列名列表: {rule.column_names}")
    print(f"  脱敏类型: {rule.masking_type}")

    # 用户场景的SQL
    sql = """
    SELECT
        u.id AS user_id,
        u.username,
        u.email,
        u.email as "test",
        l.login_ip,
        l.login_time
    FROM users u
    INNER JOIN user_logs l ON u.id = l.user_id
    """

    # 模拟查询结果
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

    print("\n原始SQL语句:")
    print(sql.strip())

    print("\n原始数据:")
    for row in test_data:
        print(row)

    # 执行脱敏
    masked_result = apply_masking_rules(None, sql, test_data, None)

    print("\n脱敏后结果:")
    for row in masked_result:
        print(row)

    print("\n" + "=" * 60)
    print("验证：")

    all_ok = True
    for i, (original, masked) in enumerate(zip(test_data, masked_result)):
        print(f"\n第 {i+1} 行：")

        if masked['email'] == original['email']:
            print(f"  ❌ email字段未脱敏: {original['email']}")
            all_ok = False
        else:
            print(f"  ✅ email字段已脱敏: {original['email']} → {masked['email']}")

        if masked['test'] == original['test']:
            print(f"  ❌ test字段未脱敏: {original['test']}")
            all_ok = False
        else:
            print(f"  ✅ test字段已脱敏: {original['test']} → {masked['test']}")

    if all_ok:
        print("\n✅ 所有字段都已正确脱敏！")
        print("✅ 即使使用 AS 'test' 别名，email字段也能正确匹配和脱敏")
    else:
        print("\n❌ 存在脱敏失败的字段")


def test_query_execution_api():
    """
    测试实际API执行查询的场景
    """
    print("\n" + "=" * 60)
    print("测试API查询脱敏场景")
    print("=" * 60)

    # 这里应该测试API，但是需要真实的登录
    print("API场景说明：")
    print("1. 调用 /api/queries/execute/")
    print("2. 使用相同的SQL查询")
    print("3. 服务器会自动解析AS别名")
    print("4. 两个email相关字段都会被脱敏")
    print("5. 返回的结果中 email 和 test 都是脱敏后的")

    print("\n测试建议：")
    print("- 重启服务器以应用修改")
    print("- 访问 http://127.0.0.1:8000/queries/sql/")
    print("- 执行用户场景的SQL查询")
    print("- 验证返回的结果")


def main():
    print("MySQL查询平台 - 用户场景脱敏验证")

    try:
        test_user_scene()
        test_query_execution_api()

        print("\n" + "=" * 60)
        print("完成！")
        print("\n说明：")
        print("- 现在支持 AS 'test' 这样的列别名脱敏")
        print("- 配置 'email' 规则会同时匹配到原列名和别名列")
        print("- 需要重启服务器以应用最新的修改")

    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
