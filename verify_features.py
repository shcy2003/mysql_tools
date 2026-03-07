#!/usr/bin/env python3
"""
MySQL查询平台 - 功能验证脚本
用于快速验证主要功能是否正常工作
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"  ✅ {message}")

def print_error(message):
    print(f"  ❌ {message}")

def print_info(message):
    print(f"  ℹ️  {message}")

def check_login_page():
    print_header("验证登录页面")
    try:
        response = requests.get(f"{BASE_URL}/accounts/login/")
        if response.status_code == 200:
            print_success("登录页面可以正常访问")
            content = response.text
            if 'navbar' in content.lower():
                print_error("发现导航栏，应该隐藏")
            else:
                print_success("导航栏已隐藏")
            if 'sidebar' in content.lower():
                print_error("发现侧边栏，应该隐藏")
            else:
                print_success("侧边栏已隐藏")
            if 'login-card' in content or 'login-wrapper' in content:
                print_success("登录卡片存在")
            return True
        else:
            print_error(f"登录页面无法访问，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"登录页面验证失败: {e}")
        return False

def check_api_endpoint(url, name, expected_status=200, check_login=False):
    print_header(f"验证 {name}")
    try:
        response = requests.get(url, allow_redirects=True)
        if check_login and 'accounts/login' in response.url:
            print_info(f"需要登录 - 这是正常的")
            return True
        if response.status_code == expected_status:
            print_success(f"{name} 可以正常访问")
            return True
        else:
            print_error(f"{name} 无法访问，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{name} 验证失败: {e}")
        return False

def check_static_files():
    print_header("验证静态文件")
    static_files = [
        ("/static/css/styles.css", "CSS文件"),
        ("/static/js/main.js", "JS文件"),
    ]
    for path, name in static_files:
        try:
            response = requests.get(f"{BASE_URL}{path}")
            if response.status_code == 200:
                print_success(f"{name} 可以正常加载")
            else:
                print_error(f"{name} 无法加载，状态码: {response.status_code}")
        except Exception as e:
            print_error(f"{name} 加载失败: {e}")

def check_server_status():
    print_header("服务器状态检查")
    try:
        response = requests.get(f"{BASE_URL}")
        if response.status_code in [200, 301, 302]:
            print_success(f"服务器正在运行")
            return True
        else:
            print_error(f"服务器响应异常，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"无法连接到服务器: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  MySQL查询平台 - 功能验证工具")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')")
    print("="*60)

    results = []

    results.append(check_server_status())
    results.append(check_login_page())
    results.append(check_api_endpoint(f"{BASE_URL}/", "首页", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/queries/sql/", "SQL查询页面", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/connections/", "连接管理页面", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/queries/history/", "查询历史页面", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/desensitization/", "脱敏规则页面", check_login=True))

    print("\n" + "="*60)
    print("  API端点验证")
    print("="*60)

    results.append(check_api_endpoint(f"{BASE_URL}/api/connections/tree/", "连接树API"))
    results.append(check_api_endpoint(f"{BASE_URL}/api/queries/table_structure/", "表结构API"))
    results.append(check_api_endpoint(f"{BASE_URL}/api/queries/export_excel/", "导出ExcelAPI"))

    check_static_files()

    print("\n" + "="*60)
    print("  验证结果汇总")
    print("="*60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n  总计: {total} 项")
    print(f"  通过: {passed} 项")
    print(f"  失败: {failed} 项")

    if failed == 0:
        print("\n  🎉 所有验证通过！")
    else:
        print(f"\n  ⚠️  有 {failed} 项验证失败，请检查")

    print("\n" + "="*60 + "\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
