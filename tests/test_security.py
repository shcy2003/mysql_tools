"""
安全测试模块 - SQL注入漏洞验证

本模块包含针对SQL注入漏洞的安全测试用例。
Bug-001: queries/views.py 中的 build_query() 函数存在SQL注入漏洞
Bug-002: connections/utils.py 中的 get_columns() 函数存在SQL注入漏洞

作者: 测试工程师Agent
创建日期: 2026-03-03
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def check_build_query_vulnerability():
    """
    检查build_query函数是否存在SQL注入漏洞
    
    返回: (是否修复, 详细信息)
    """
    views_file = os.path.join(PROJECT_ROOT, 'queries', 'views.py')
    with open(views_file, 'r') as f:
        content = f.read()
    
    # 检查是否使用了参数化查询（修复的标志）
    if '%s' in content and 'return sql, params' in content:
        # 检查是否同时存在白名单验证
        if 're.match' in content and r'^[a-zA-Z_]' in content:
            return True, "使用参数化查询 + 白名单验证"
        return True, "使用参数化查询"
    
    # 检查是否存在漏洞代码模式
    if "'{cond['value']}'" in content:
        return False, "发现直接字符串拼接: {cond['value']}"
    
    if "f\"{cond['field']}" in content or "f'{cond['field']}" in content:
        return False, "发现f-string拼接"
    
    if "f\"{cond[" in content or "'" + "{cond[" in content:
        return False, "发现字符串格式化"
    
    return None, "无法确定状态"


def check_get_columns_vulnerability():
    """
    检查get_columns函数是否存在SQL注入漏洞
    
    返回: (是否修复, 详细信息)
    """
    utils_file = os.path.join(PROJECT_ROOT, 'connections', 'utils.py')
    with open(utils_file, 'r') as f:
        content = f.read()
    
    # 检查是否有白名单验证（修复的标志）
    if 're.match' in content and r'^[a-zA-Z_][a-zA-Z0-9_]*$' in content:
        return True, "使用表名白名单验证"
    
    # 检查是否使用了参数化查询（另一种修复方式）
    if '%s' in content and 'DESCRIBE' in content:
        return True, "使用参数化查询"
    
    # 检查是否存在漏洞代码模式
    if 'f"DESCRIBE {table_name}"' in content:
        return False, "发现f-string拼接: f\"DESCRIBE {table_name}\""
    
    if 'f\'DESCRIBE {table_name}\'' in content:
        return False, "发现f-string拼接: f'DESCRIBE {table_name}'"
    
    if "DESCRIBE {table_name}" in content and 'f"' in content:
        return False, "发现DESCRIBE字符串格式化"
    
    return None, "无法确定状态"


def run_security_tests():
    """
    运行安全测试并生成报告
    """
    print("=" * 70)
    print("SQL注入漏洞安全测试报告")
    print("=" * 70)
    print(f"测试时间: {os.popen('date').read().strip()}")
    print(f"项目路径: {PROJECT_ROOT}")
    print()
    
    # 测试Bug-001
    print("-" * 70)
    print("[Bug-001] build_query() 函数SQL注入漏洞检测")
    print("-" * 70)
    
    fixed, details = check_build_query_vulnerability()
    
    if fixed is True:
        print(f"状态: [FIXED] 已修复")
        print(f"详情: {details}")
        bug001_status = "FIXED"
    elif fixed is False:
        print(f"状态: [VULNERABLE] 存在漏洞")
        print(f"详情: {details}")
        bug001_status = "VULNERABLE"
    else:
        print(f"状态: [UNKNOWN] 无法确定")
        print(f"详情: {details}")
        bug001_status = "UNKNOWN"
    
    print()
    
    # 测试Bug-002
    print("-" * 70)
    print("[Bug-002] get_columns() 函数SQL注入漏洞检测")
    print("-" * 70)
    
    fixed, details = check_get_columns_vulnerability()
    
    if fixed is True:
        print(f"状态: [FIXED] 已修复")
        print(f"详情: {details}")
        bug002_status = "FIXED"
    elif fixed is False:
        print(f"状态: [VULNERABLE] 存在漏洞")
        print(f"详情: {details}")
        bug002_status = "VULNERABLE"
    else:
        print(f"状态: [UNKNOWN] 无法确定")
        print(f"详情: {details}")
        bug002_status = "UNKNOWN"
    
    print()
    
    # 生成总结报告
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    
    vulnerabilities = []
    if bug001_status == "VULNERABLE":
        vulnerabilities.append("Bug-001: build_query() SQL注入")
    if bug002_status == "VULNERABLE":
        vulnerabilities.append("Bug-002: get_columns() SQL注入")
    
    if vulnerabilities:
        print("[ALERT] 发现安全漏洞!")
        print()
        print("漏洞列表:")
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"  {i}. {vuln}")
        print()
        print("建议:")
        print("  1. 立即使用参数化查询修复SQL注入漏洞")
        print("  2. 对用户输入进行白名单验证")
        print("  3. 部署前进行安全测试")
    else:
        print("[OK] 未发现明显的SQL注入漏洞")
        if bug001_status == "FIXED":
            print("  ✓ Bug-001 (build_query): 已修复")
        if bug002_status == "FIXED":
            print("  ✓ Bug-002 (get_columns): 已修复")
    
    print()
    print("=" * 70)
    
    return len(vulnerabilities)


if __name__ == '__main__':
    try:
        exit_code = run_security_tests()
        sys.exit(exit_code)
    except Exception as e:
        print(f"[ERROR] 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
