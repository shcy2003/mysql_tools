#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自动化访问所有页面（登录后）并检查错误"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# 确保有测试用户
if not User.objects.filter(username='testuser').exists():
    User.objects.create_superuser('testuser', 'test@test.com', 'testpass123')
    print("Created test superuser: testuser / testpass123")

# 创建测试客户端并登录
client = Client()
user = client.login(username='testuser', password='testpass123')
if not user:
    print("Login failed!")
    sys.exit(1)
print("Logged in as testuser")

# 所有需要测试的 URL
urls = [
    '/queries/',
    '/queries/sql/',
    '/queries/sql/new/',
    '/queries/history/',
    '/connections/',
    '/connections/create/',
    '/audit/',
    '/desensitization/',
    '/desensitization/create/',
    '/accounts/profile/',
]

print("=" * 60)
print("Automation Page Test (Authenticated)")
print("=" * 60)

errors = []
for url in urls:
    try:
        response = client.get(url)
        status = response.status_code
        result = f"[{status}] {url}"

        if status == 500:
            print(result + " - ERROR 500")
            errors.append((url, status, "Server Internal Error"))
        elif status >= 400:
            print(result + f" - ERROR {status}")
            errors.append((url, status, f"HTTP {status}"))
        else:
            print(result + " - OK")
    except Exception as e:
        print(f"[ERROR] {url} - {str(e)}")
        errors.append((url, 0, str(e)))

print()
print("=" * 60)
if errors:
    print(f"Found {len(errors)} issues:")
    for url, status, msg in errors:
        print(f"  - {url}: {msg}")
else:
    print("All pages are accessible!")

print("=" * 60)