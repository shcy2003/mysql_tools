from django.contrib import admin
from .models import QueryHistory, SystemConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """系统配置后台管理"""
    list_display = ['name', 'value', 'description', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['value']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        """禁止删除系统配置项"""
        return False


@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    """查询历史后台管理"""
    list_display = ['user', 'connection', 'created_at', 'execution_time']
    list_filter = ['created_at', 'user', 'connection']
    search_fields = ['user__username', 'sql']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

