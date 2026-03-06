from django.db import models
from django.conf import settings


class MaskingRule(models.Model):
    """脱敏规则模型（全局配置）"""
    MASKING_TYPE_CHOICES = (
        ('full', '完全脱敏'),
        ('partial', '部分脱敏'),
        ('regex', '正则匹配'),
    )

    # 规则名称
    name = models.CharField(max_length=100, default='', verbose_name='规则名称')
    # 全局配置，不需要指定连接和表名
    column_names = models.JSONField(default=list, verbose_name='列名列表')
    masking_type = models.CharField(
        max_length=20,
        choices=MASKING_TYPE_CHOICES,
        verbose_name='脱敏类型'
    )
    masking_params = models.JSONField(blank=True, null=True, verbose_name='脱敏参数')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='masking_rules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '脱敏规则'
        verbose_name_plural = '脱敏规则'

    def __str__(self):
        return f"{self.name} - {self.masking_type}"