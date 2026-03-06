from django.db import models
from django.conf import settings
from connections.models import MySQLConnection


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
    sql = models.TextField(verbose_name='SQL 语句')
    execution_time = models.FloatField(null=True, blank=True, verbose_name='执行时间(ms)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '查询历史'
        verbose_name_plural = '查询历史'

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"