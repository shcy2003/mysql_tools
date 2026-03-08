"""
初始化系统配置命令
"""
from django.core.management.base import BaseCommand
from queries.models import SystemConfig


class Command(BaseCommand):
    help = '初始化系统配置项'

    def handle(self, *args, **options):
        """处理命令"""
        configs = [
            {
                'name': 'tables_per_page',
                'value': '5',
                'description': '左边栏每页显示的表数量'
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
                self.stdout.write(self.style.SUCCESS(
                    f'创建配置: {config.name} = {config.value}'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'配置已存在: {config.name}，跳过'
                ))

        self.stdout.write(self.style.SUCCESS('系统配置初始化完成！'))
