#!/usr/bin/env python3
"""
SQL注入漏洞验证脚本
用于验证Bug-001和Bug-002漏洞的存在性

使用方法: python3 test_security_verify.py
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

# 读取build_query函数的源代码并执行
def get_build_query_func():
    """动态获取build_query函数"""
    views_file = os.path.join(PROJECT_ROOT, 'queries', 'views.py')
    with open(views_file, 'r') as f:
        content = f.read()
    
    # 提取build_query函数
    start = content.find('def build_query(')
    end = content.find('def get_available_connections(')
    func_code = content[start:end]
    
    # 执行函数定义
    local_ns = {}
    exec(func_code, local_ns)
    return local_ns['build_query']


def get_get_columns_func():
    """动态获取get_columns函数"""
    utils_file = os.path.join(PROJECT_ROOT, 'connections', 'utils.py')
    with open(utils_file, 'r') as f:
        content = f.read()
    
    # 提取get_columns函数
    start = content.find('def get_columns(')
    end = content.find('def get_columns', start + 1) if content.find('def get_columns', start + 1) > 0 else len(content)
    func_code = content[start:end]
    
    return func_code


def main():
    """主测试函数"""
    print("=" * 70)
    print("SQL注入漏洞验证测试")
    print("=" * 70)
    print()
    
    # 获取build_query函数
    try:
        build_query = get_build_query_func()
        print("[OK] 成功加载build_query函数")
    except Exception as e:
        print(f"[ERROR] 加载build_query函数失败: {e}")
        return 1
    
    print()
    
    # ========== 测试1: 基本SQL注入 ==========
    print("[Test 1] 基本SQL注入 - 条件绕过")
    print("-" * 50)
    conditions = [
        {
            'field': 'username',
            'operator': '=',
            'value': "' OR '1'='1"
        }
    ]
    
    sql = build_query('users', ['id', 'username'], conditions)
    print(f"恶意输入: \"' OR '1'='1\"")
    print(f"生成的SQL: {sql}")
    
    # 验证漏洞存在
    if "' OR '1'='1" in sql and "'" in sql.split("OR")[0]:
        print("[VULNERABLE] 漏洞确认: SQL注入成功，恶意代码被直接拼接")
        test1_passed = True
    else:
        print("[SAFE] 漏洞已修复: 输入被正确处理")
        test1_passed = False
    print()
    
    # ========== 测试2: UNION注入 ==========
    print("[Test 2] UNION SELECT注入")
    print("-" * 50)
    conditions = [
        {
            'field': 'id',
            'operator': '=',
            'value': "1' UNION SELECT username, password FROM admin_users-- "
        }
    ]
    
    sql = build_query('users', ['id', 'name'], conditions)
    print(f"恶意输入: \"1' UNION SELECT username, password FROM admin_users-- \"")
    print(f"生成的SQL: {sql}")
    
    if "UNION" in sql.upper() and "admin_users" in sql:
        print("[VULNERABLE] 漏洞确认: UNION注入成功")
        test2_passed = True
    else:
        print("[SAFE] 漏洞已修复")
        test2_passed = False
    print()
    
    # ========== 测试3: LIKE注入 ==========
    print("[Test 3] LIKE操作符注入")
    print("-" * 50)
    conditions = [
        {
            'field': 'name',
            'operator': 'like',
            'value': "%' OR 1=1-- "
        }
    ]
    
    sql = build_query('products', ['id', 'name'], conditions)
    print(f"恶意输入: \"%' OR 1=1-- \"")
    print(f"生成的SQL: {sql}")
    
    if "OR 1=1" in sql or "%' OR" in sql:
        print("[VULNERABLE] 漏洞确认: LIKE注入成功")
        test3_passed = True
    else:
        print("[SAFE] 漏洞已修复")
        test3_passed = False
    print()
    
    # ========== 测试4: get_columns注入 ==========
    print("[Test 4] get_columns() 函数注入 (Bug-002)")
    print("-" * 50)
    
    # 读取get_columns函数代码进行静态分析
    get_columns_code = get_get_columns_func()
    
    print("分析get_columns函数代码...")
    
    # 检查是否存在字符串格式化
    if 'f"DESCRIBE {table_name}"' in get_columns_code or 'DESCRIBE' in get_columns_code and 'table_name' in get_columns_code:
        print("[VULNERABLE] 漏洞确认: 发现直接字符串拼接")
        
        # 模拟攻击
        malicious_table = "users; DROP TABLE users-- "
        # 模拟代码中的执行
        expected_sql = f"DESCRIBE {malicious_table}"
        print(f"模拟恶意输入: {malicious_table}")
        print(f"生成的SQL: {expected_sql}")
        
        if "DROP TABLE" in expected_sql and ";" in expected_sql:
            print("[VULNERABLE] 漏洞确认: SQL注入成功")
            test4_passed = True
        else:
            print("[SAFE] 漏洞已修复")
            test4_passed = False
    else:
        print("[SAFE] 未检测到明显漏洞")
        test4_passed = False
    print()
    
    # ========== 总结 ==========
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    
    vulnerabilities_found = sum([test1_passed, test2_passed, test3_passed, test4_passed])
    
    print(f"发现的漏洞数: {vulnerabilities_found}/4")
    print()
    print("详细结果:")
    print(f"  [Test 1] 基本SQL注入:       {'VULNERABLE' if test1_passed else 'SAFE'}")
    print(f"  [Test 2] UNION注入:         {'VULNERABLE' if test2_passed else 'SAFE'}")
    print(f"  [Test 3] LIKE操作符注入:   {'VULNERABLE' if test3_passed else 'SAFE'}")
    print(f"  [Test 4] get_columns注入:  {'VULNERABLE' if test4_passed else 'SAFE'}")
    print()
    
    if vulnerabilities_found > 0:
        print("[!] 警告: 发现SQL注入漏洞，请立即修复！")
        print("[!] 修复建议: 使用参数化查询替换字符串拼接")
        return 1
    else:
        print("[✓] 所有测试通过，未发现SQL注入漏洞")
        return 0


if __name__ == '__main__':
    exit(main())
