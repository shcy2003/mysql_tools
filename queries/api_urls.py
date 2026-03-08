"""
查询模块API路由配置
"""
from django.urls import path
from . import api_views

app_name = 'queries_api'

urlpatterns = [
    # 通用数据查询API - 支持分页、排序、筛选
    path('data/', api_views.api_query_data, name='api_query_data'),
    # SQL查询执行API（新SQL查询界面）
    path('execute/', api_views.api_execute_query, name='api_execute_query'),
    # 获取表结构API
    path('table_structure/', api_views.api_get_table_structure, name='api_table_structure'),
    # 导出Excel API
    path('export_excel/', api_views.api_export_excel, name='api_export_excel'),
    # 获取系统配置API
    path('configs/', api_views.api_get_configs, name='api_get_configs'),
    # 保存查询API
    path('saved/', api_views.api_saved_queries, name='api_saved_queries'),
]
