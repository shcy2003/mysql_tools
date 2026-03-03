from django.contrib.auth.models import AbstractUser
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

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username