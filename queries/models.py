from django.db import models
from django.conf import settings
from connections.models import MySQLConnection


class SystemConfig(models.Model):
    """系统配置模型 - 用于Django后台配置"""
    name = models.CharField(max_length=100, unique=True, verbose_name='配置项名称')
    value = models.CharField(max_length=200, verbose_name='配置值')
    description = models.TextField(blank=True, verbose_name='配置项描述')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'

    def __str__(self):
        return f"{self.name}: {self.value}"

    @classmethod
    def get_value(cls, name, default=None):
        """获取配置值，不存在时返回默认值"""
        try:
            return cls.objects.get(name=name).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def get_int_value(cls, name, default=0):
        """获取整数类型配置值"""
        value = cls.get_value(name, str(default))
        try:
            return int(value)
        except ValueError:
            return default


class QueryHistory(models.Model):
    """查询历史模型"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='query_history'
    )
    connection = models.ForeignKey(
        MySQLConnection,
        on_delete=models.CASCADE,
        related_name='query_history'
    )
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='环境'
    )
    sql = models.TextField(verbose_name='SQL 语句')
    execution_time = models.FloatField(null=True, blank=True, verbose_name='执行时间(ms)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '查询历史'
        verbose_name_plural = '查询历史'

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class SavedQuery(models.Model):
    """保存的SQL查询模型"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_queries'
    )
    name = models.CharField(max_length=200, verbose_name='查询名称')
    sql = models.TextField(verbose_name='SQL 语句')
    connection = models.ForeignKey(
        MySQLConnection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saved_queries'
    )
    database = models.CharField(max_length=200, blank=True, verbose_name='数据库名')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '保存的查询'
        verbose_name_plural = '保存的查询'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"