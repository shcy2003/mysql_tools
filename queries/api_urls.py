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
]
