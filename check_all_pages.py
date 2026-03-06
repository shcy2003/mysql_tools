#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全面检查所有页面状态"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

# 确保有测试用户
if not User.objects.filter(username='testuser').exists():
    User.objects.create_superuser('testuser', 'test@test.com', 'testpass123')
    print("Created test superuser: testuser / testpass123")

# 所有页面 URL
all_urls = [
    # 公开页面 - 未登录访问
    ('/accounts/login/', False, 'public'),

    # 受保护页面 - 登录后访问
    ('/', True, 'authenticated'),
    ('/queries/', True, 'authenticated'),
    ('/queries/sql/', True, 'authenticated'),
    ('/queries/sql/new/', True, 'authenticated'),
    ('/queries/history/', True, 'authenticated'),
    ('/connections/', True, 'authenticated'),
    ('/connections/create/', True, 'authenticated'),
    ('/audit/', True, 'authenticated'),
    ('/desensitization/', True, 'authenticated'),
    ('/desensitization/create/', True, 'authenticated'),
    ('/accounts/profile/', True, 'authenticated'),
]

print("=" * 70)
print("Page Status Check")
print("=" * 70)

all_errors = []

# 测试每个页面
for url, requires_login, page_type in all_urls:
    # 为每个请求创建新的客户端
    client = Client()

    if requires_login:
        # 登录后再访问
        client.login(username='testuser', password='testpass123')

    try:
        response = client.get(url)
        status = response.status_code

        # 对于受保护的页面，302 重定向是正常的（未登录时）
        if page_type == 'authenticated' and status == 302:
            # 检查重定向到哪里
            if 'login' in response.url or 'accounts/login' in response.url:
                print(f"[REDIRECT] {url} -> {response.url} (未登录重定向是正常的)")
            else:
                print(f"[OK] {url} - HTTP {status} (redirect to {response.url})")
        elif status >= 400:
            print(f"[ERROR] {url} - HTTP {status}")
            all_errors.append((url, status))
        else:
            print(f"[OK] {url} - HTTP {status}")
    except Exception as e:
        print(f"[ERROR] {url} - {str(e)}")
        all_errors.append((url, str(e)))

print("\n" + "=" * 70)
if all_errors:
    print(f"Found {len(all_errors)} issues:")
    for url, error in all_errors:
        print(f"  - {url}: {error}")
    sys.exit(1)
else:
    print("All pages are accessible!")
    print("=" * 70)
    sys.exit(0)