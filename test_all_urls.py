#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全面检查所有 URL 路由状态"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.urls import get_resolver

# 获取所有 URL
resolver = get_resolver()

def get_all_urlspatterns(urlpatterns, prefix=''):
    """递归获取所有 URL 模式"""
    urls = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # 这是一个 include，需要递归
            urls.extend(get_all_urlspatterns(pattern.url_patterns, prefix + str(pattern.pattern)))
        else:
            # 这是一个具体的 URL
            url = prefix + str(pattern.pattern)
            # 清理 URL 模式（移除 <...> 部分）
            url = url.replace('<', '{').replace('>', '}')
            urls.append({
                'url': url,
                'name': getattr(pattern, 'name', None),
                'callback': pattern.callback
            })
    return urls

# 获取所有 URL
all_urls = get_all_urlspatterns(resolver.url_patterns)

print("=" * 70)
print("All URLs in the project:")
print("=" * 70)
for u in all_urls:
    name = u['name'] if u['name'] else '(no name)'
    print(f"{u['url']:50} -> {name}")

print()
print("=" * 70)
print("Checking login URL specifically:")
print("=" * 70)

# 尝试解析 /accounts/login/
try:
    from django.urls import reverse
    url = reverse('accounts:login')
    print(f"accounts:login resolves to: {url}")
except Exception as e:
    print(f"Error resolving accounts:login: {e}")