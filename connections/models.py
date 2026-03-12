from django.db import models
from django.conf import settings


class MySQLConnection(models.Model):
    """MySQL 连接配置模型"""
    STATUS_CHOICES = [
        ('active', '已连接'),
        ('inactive', '未连接'),
    ]

    name = models.CharField(max_length=100, verbose_name='连接名称')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='inactive',
        verbose_name='连接状态'
    )
    host = models.CharField(max_length=255, verbose_name='主机地址')
    port = models.PositiveIntegerField(default=3306, verbose_name='端口')
    database = models.CharField(max_length=100, verbose_name='数据库名称')
    username = models.CharField(max_length=100, verbose_name='用户名')
    password = models.CharField(max_length=255, verbose_name='密码')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='connections'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='所属环境'
    )

    class Meta:
        verbose_name = 'MySQL 连接'
        verbose_name_plural = 'MySQL 连接'

    def __str__(self):
        return self.name

    def get_connection_params(self):
        """获取连接参数"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password,
        }