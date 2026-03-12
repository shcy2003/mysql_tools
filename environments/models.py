from django.db import models


class Environment(models.Model):
    """环境模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='环境名称')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '环境'
        verbose_name_plural = '环境'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
