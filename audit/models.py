from django.db import models
from django.conf import settings
from connections.models import MySQLConnection


class AuditLog(models.Model):
    """审计日志模型"""
    ACTION_CHOICES = (
        ('query', '查询'),
        ('login', '登录'),
        ('logout', '登出'),
        ('create_connection', '创建连接'),
        ('update_connection', '更新连接'),
        ('delete_connection', '删除连接'),
        ('create_masking', '创建脱敏规则'),
        ('update_masking', '更新脱敏规则'),
        ('delete_masking', '删除脱敏规则'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    connection = models.ForeignKey(
        MySQLConnection,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='环境'
    )
    sql = models.TextField(null=True, blank=True, verbose_name='SQL 语句')
    execution_time = models.FloatField(null=True, blank=True, verbose_name='执行时间(ms)')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP 地址')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at}"