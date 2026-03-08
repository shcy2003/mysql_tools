#!/usr/bin/env python
"""
初始化系统配置项 - 将默认配置添加到数据库
"""
import os
import django

# 配置Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from queries.models import SystemConfig


def init_system_configs():
    """初始化系统配置"""
    configs = [
        {
            'name': 'tables_per_page',
            'value': '5',
            'description': '左边栏每页显示的表数量'
        },
        {
            'name': 'sql_query_page_size',
            'value': '20',
            'description': 'SQL查询结果每页显示的记录数'
        },
        {
            'name': 'max_pagination_pages',
            'value': '3',
            'description': '分页控件最多显示的页码数量'
        },
        {
            'name': 'sidebar_default_width',
            'value': '250',
            'description': '侧边栏默认宽度(px)'
        },
        {
            'name': 'sidebar_min_width',
            'value': '100',
            'description': '侧边栏最小宽度(px)'
        },
        {
            'name': 'sidebar_max_width',
            'value': '600',
            'description': '侧边栏最大宽度(px)'
        },
    ]

    for config_data in configs:
        config, created = SystemConfig.objects.get_or_create(
            name=config_data['name'],
            defaults={
                'value': config_data['value'],
                'description': config_data['description']
            }
        )
        if created:
            print(f'创建配置: {config.name} = {config.value}')
        else:
            print(f'配置已存在: {config.name}，跳过')

    print('系统配置初始化完成！')


if __name__ == '__main__':
    init_system_configs()
