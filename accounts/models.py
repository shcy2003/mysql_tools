from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):
    """自定义用户模型"""
    ROLE_CHOICES = (
        ('normal', '普通用户'),
        ('admin', '管理员'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='normal')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='上次登录IP')
    login_count = models.PositiveIntegerField(default=0, verbose_name='登录次数')
    environments = models.ManyToManyField('environments.Environment', blank=True, verbose_name='可访问环境')

    # 显式定义 groups 和 user_permissions 字段，避免与 auth.User 冲突
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username