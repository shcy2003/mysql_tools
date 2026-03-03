from django.db import models
from connections.models import MySQLConnection


class MaskingRule(models.Model):
    """脱敏规则模型"""
    MASKING_TYPE_CHOICES = (
        ('full', '完全脱敏'),
        ('partial', '部分脱敏'),
        ('regex', '正则匹配'),
    )

    connection = models.ForeignKey(
        MySQLConnection,
        on_delete=models.CASCADE,
        related_name='masking_rules'
    )
    table_name = models.CharField(max_length=100, verbose_name='表名')
    column_name = models.CharField(max_length=100, verbose_name='列名')
    masking_type = models.CharField(
        max_length=20,
        choices=MASKING_TYPE_CHOICES,
        verbose_name='脱敏类型'
    )
    masking_params = models.JSONField(blank=True, null=True, verbose_name='脱敏参数')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '脱敏规则'
        verbose_name_plural = '脱敏规则'
        unique_together = ('connection', 'table_name', 'column_name')

    def __str__(self):
        return f"{self.connection.name} - {self.table_name}.{self.column_name}"