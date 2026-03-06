#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自动化访问所有页面并检查错误"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.test import Client

# 创建测试客户端
client = Client()

# 所有需要测试的 URL
urls = [
    # 公开页面
    '/accounts/login/',

    # 需要登录的页面
    '/queries/',
    '/queries/sql/',
    '/queries/history/',
    '/connections/',
    '/connections/create/',
    '/audit/',
    '/desensitization/',
    '/desensitization/create/',
]

print("=" * 60)
print("Automation Page Test")
print("=" * 60)

errors = []
for url in urls:
    try:
        response = client.get(url)
        status = response.status_code
        result = f"[{status}] {url}"

        # 检查是否有模板错误或异常
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