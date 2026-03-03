from django.contrib.auth import get_user_model
from django.db import transaction


def create_superuser():
    User = get_user_model()

    with transaction.atomic():
        # 检查是否已存在超级用户
        if User.objects.filter(username='admin').exists():
            print("超级用户 'admin' 已存在")
            return

        # 创建超级用户
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        admin_user.save()

        print("超级用户 'admin' 创建成功")


if __name__ == "__main__":
    import django
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
    django.setup()

    create_superuser()