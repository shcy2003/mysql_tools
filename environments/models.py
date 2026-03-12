from django.db import models
import hashlib


class Environment(models.Model):
    """环境模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='环境名称')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    color = models.CharField(max_length=20, blank=True, verbose_name='标签颜色')

    class Meta:
        verbose_name = '环境'
        verbose_name_plural = '环境'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.color:
            self.color = self.generate_color()
        super().save(*args, **kwargs)

    def generate_color(self):
        """根据环境名称生成唯一颜色"""
        colors = [
            '#28a745', '#17a2b8', '#007bff', '#6f42c1', '#e83e8c',
            '#fd7e14', '#20c997', '#6c757d', '#343a40', '#dc3545',
            '#6610f2', '#e0a800', '#d63384', '#0dcaf0', '#198754'
        ]
        hash_value = int(hashlib.md5(self.name.encode()).hexdigest(), 16)
        return colors[hash_value % len(colors)]
