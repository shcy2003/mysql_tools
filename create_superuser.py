#!/usr/bin/env python
"""
直接创建 Django 超级用户的脚本
"""

import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from accounts.models import User

def create_superuser():
    """创建超级用户"""
    # 检查是否已存在超级用户
    if User.objects.filter(username='admin', is_superuser=True).exists():
        print("超级用户 admin 已存在")
        return

    # 创建超级用户
    try:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123456'
        )
        user.role = 'admin'
        user.save()
        print("超级用户创建成功:")
        print(f"  用户名: admin")
        print(f"  密码: admin123456")
        print(f"  邮箱: admin@example.com")
        print(f"  角色: 管理员")
        return user
    except Exception as e:
        print(f"创建超级用户失败: {str(e)}")
        return None

if __name__ == "__main__":
    create_superuser()
