#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有 API 接口"""
import os
import sys
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.test import Client

print("=" * 70)
print("API Status Check")
print("=" * 70)

# 测试 GET 端点
get_apis = [
    ('/api/connections/tree/', 'GET', None),
    ('/api/connections/1/databases/', 'GET', None),
    ('/api/connections/1/tables/', 'GET', None),
    ('/api/health/', 'GET', None),
    ('/api/health/db/', 'GET', None),
    ('/api/health/db/stats/', 'GET', None),
]

all_errors = []

# 测试 GET API
print("\n[GET APIs]")
for url, method, data in get_apis:
    try:
        client = Client()
        client.login(username='testuser', password='testpass123')

        if method == 'GET':
            response = client.get(url)
        else:
            response = client.post(url, data=data, content_type='application/json')

        status = response.status_code

        if status >= 400:
            print(f"[ERROR] {url} - HTTP {status}")
            all_errors.append((url, status))
        else:
            print(f"[OK] {url} - HTTP {status}")
    except Exception as e:
        print(f"[ERROR] {url} - {str(e)}")
        all_errors.append((url, str(e)))

# 测试 /api/queries/data/ API (需要参数)
print("\n[Queries Data API]")
try:
    client = Client()
    client.login(username='testuser', password='testpass123')

    # 缺少必需参数应该返回 400
    response = client.get('/api/queries/data/')
    print(f"[INFO] /api/queries/data/ (no params) - HTTP {response.status_code}")

    # 有参数的情况
    response = client.get('/api/queries/data/?connection_id=1&table=users')
    print(f"[INFO] /api/queries/data/?connection_id=1&table=users - HTTP {response.status_code}")
    if response.status_code >= 400:
        content = json.loads(response.content)
        print(f"       Response: {content.get('message', 'error')[:100]}")

except Exception as e:
    print(f"[ERROR] /api/queries/data/ - {str(e)}")

# 测试 /api/queries/execute/ API (只接受 POST)
print("\n[Queries Execute API]")
try:
    client = Client()
    client.login(username='testuser', password='testpass123')

    # POST 请求
    response = client.post('/api/queries/execute/',
                          data=json.dumps({'connection_id': 1, 'sql': 'SELECT 1'}),
                          content_type='application/json')
    if response.status_code >= 400:
        content = json.loads(response.content)
        print(f"[INFO] POST /api/queries/execute/ - HTTP {response.status_code}")
        print(f"       Response: {content.get('message', 'error')[:100]}")
    else:
        print(f"[OK] POST /api/queries/execute/ - HTTP {response.status_code}")

except Exception as e:
    print(f"[ERROR] POST /api/queries/execute/ - {str(e)}")
    all_errors.append(('/api/queries/execute/', str(e)))

print("\n" + "=" * 70)
if all_errors:
    print(f"Found {len(all_errors)} critical issues:")
    for url, error in all_errors:
        print(f"  - {url}: {error}")
else:
    print("All critical APIs are accessible!")
print("=" * 70)