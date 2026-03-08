#!/usr/bin/env python
"""检查用户和连接信息"""

import os
import django

# 初始化Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from connections.models import MySQLConnection
from accounts.models import User

print("=== Users ===")
users = User.objects.all()
for user in users:
    print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}")

print("\n=== Connections ===")
conns = MySQLConnection.objects.all()
for conn in conns:
    print(f"ID: {conn.id}, Name: {conn.name}, Created by: {conn.created_by_id}")
