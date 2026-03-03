from django.db import models
from django.conf import settings


class MySQLConnection(models.Model):
    """MySQL 连接配置模型"""
    name = models.CharField(max_length=100, verbose_name='连接名称')
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