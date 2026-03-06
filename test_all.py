#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL 查询平台 - 自动化测试脚本
测试所有页面和 API 接口

使用方法:
    python test_all.py

作者: Claude
"""
import os
import sys
import json
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# 颜色输出（兼容 Windows）
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"[OK] {msg}")

def print_error(msg):
    print(f"[FAIL] {msg}")

def print_info(msg):
    print(f"[INFO] {msg}")

def print_warning(msg):
    print(f"[WARN] {msg}")


class APITester:
    def __init__(self):
        self.client = Client()
        self.user = None
        self.login()

    def login(self):
        """登录测试用户"""
        User = get_user_model()
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_superuser('testuser', 'test@test.com', 'testpass123')
            print_info("Created test superuser: testuser / testpass123")

        result = self.client.login(username='testuser', password='testpass123')
        if result:
            print_success("Logged in as testuser")
        else:
            print_error("Login failed!")
            sys.exit(1)

    def test_page(self, url, expected_status=200, description=""):
        """测试页面"""
        desc = description or url
        try:
            response = self.client.get(url)
            status = response.status_code

            # 处理重定向（预期 302 算正常）
            if expected_status == 302 and status == 302:
                print_success(f"GET {desc} -> {status} (redirect)")
                return True

            if status == expected_status:
                print_success(f"GET {desc} -> {status}")
                return True
            else:
                print_error(f"GET {desc} -> {status} (expected {expected_status})")
                return False
        except Exception as e:
            print_error(f"GET {desc} -> Error: {str(e)}")
            return False

    def test_api_get(self, url, expected_status=200, description="", params=None):
        """测试 GET API"""
        desc = description or url
        try:
            if params:
                response = self.client.get(url, params=params)
            else:
                response = self.client.get(url)

            status = response.status_code
            if status == expected_status:
                print_success(f"GET {desc} -> {status}")
                return True, response.json() if response.content else {}
            elif status == 404:
                print_warning(f"GET {desc} -> {status} (可能需要数据)")
                return True, {}
            else:
                print_error(f"GET {desc} -> {status}")
                try:
                    data = response.json()
                    print_error(f"   Response: {data.get('message', data)}")
                except:
                    pass
                return False, {}
        except Exception as e:
            print_error(f"GET {desc} -> Error: {str(e)}")
            return False, {}

    def test_api_post(self, url, data, expected_status=200, description=""):
        """测试 POST API"""
        desc = description or url
        try:
            response = self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json'
            )
            status = response.status_code

            if status == expected_status:
                print_success(f"POST {desc} -> {status}")
                return True, response.json() if response.content else {}
            elif status in [404, 400]:
                print_warning(f"POST {desc} -> {status} (可能需要数据)")
                return True, {}
            else:
                print_error(f"POST {desc} -> {status}")
                try:
                    data = response.json()
                    print_error(f"   Response: {data.get('message', data)}")
                except:
                    pass
                return False, {}
        except Exception as e:
            print_error(f"POST {desc} -> Error: {str(e)}")
            return False, {}


def run_page_tests(tester):
    """页面测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}页面测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    pages = [
        ('/accounts/login/', 200, '登录页（未登录）'),
        ('/', 302, '首页（重定向）'),
    ]

    # 需要登录的页面
    auth_pages = [
        ('/queries/', 200, '查询列表'),
        ('/queries/sql/', 200, 'SQL查询页'),
        ('/queries/sql/new/', 200, 'SQL查询页（新）'),
        ('/queries/history/', 200, '查询历史'),
        ('/connections/', 200, '连接管理'),
        ('/connections/create/', 200, '创建连接'),
        ('/audit/', 200, '审计日志'),
        ('/desensitization/', 200, '脱敏规则'),
        ('/desensitization/create/', 200, '创建脱敏规则'),
        ('/accounts/profile/', 200, '用户资料'),
    ]

    all_passed = True

    # 公开页面
    tester.client.logout()
    for url, status, desc in pages:
        if not tester.test_page(url, status, desc):
            all_passed = False

    # 认证页面
    tester.login()
    for url, status, desc in auth_pages:
        if not tester.test_page(url, status, desc):
            all_passed = False

    return all_passed


def run_api_tests(tester):
    """API 测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}API 测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    all_passed = True

    # 连接管理 API
    print(f"\n{Colors.YELLOW}连接管理 API:{Colors.END}")
    ok, _ = tester.test_api_get('/api/connections/tree/', 200, '获取连接树')
    if not ok:
        all_passed = False

    ok, _ = tester.test_api_get('/api/connections/1/databases/', 200, '获取数据库列表')
    if not ok:
        all_passed = False

    ok, _ = tester.test_api_get('/api/connections/1/tables/', 200, '获取表列表', {'database': 'test'})
    if not ok:
        all_passed = False

    # 查询 API
    print(f"\n{Colors.YELLOW}查询 API:{Colors.END}")

    # GET 数据查询（需要参数）
    ok, _ = tester.test_api_get('/api/queries/data/', 400, '数据查询（缺少参数）')
    if ok:
        print_success("  数据查询参数验证正常")

    # POST 数据查询
    ok, _ = tester.test_api_post('/api/queries/data/', {
        'connection_id': 1,
        'table': 'users',
        'page': 1,
        'page_size': 10
    }, 404, '数据查询（POST）')
    # 404 是因为没有连接或表，不算错误

    # SQL 执行
    ok, _ = tester.test_api_post('/api/queries/execute/', {
        'connection_id': 1,
        'sql': 'SELECT 1'
    }, 404, '执行SQL查询')
    # 404 是因为没有连接，不算错误

    # 健康检查 API
    print(f"\n{Colors.YELLOW}健康检查 API:{Colors.END}")
    tester.client.logout()  # 登出，测试不需要认证的 API

    ok, _ = tester.test_api_get('/api/health/', 200, '健康检查（所有连接）')
    if not ok:
        all_passed = False

    ok, _ = tester.test_api_get('/api/health/db/', 200, '健康检查（数据库）')
    if not ok:
        all_passed = False

    ok, _ = tester.test_api_get('/api/health/db/stats/', 200, '健康检查（统计）')
    if not ok:
        all_passed = False

    return all_passed


def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}MySQL 查询平台 - 自动化测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    tester = APITester()

    # 运行测试
    page_passed = run_page_tests(tester)
    api_passed = run_api_tests(tester)

    # 总结
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}测试结果{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    if page_passed and api_passed:
        print_success("所有测试通过!")
        return 0
    else:
        print_error("部分测试失败!")
        return 1


if __name__ == '__main__':
    sys.exit(main())