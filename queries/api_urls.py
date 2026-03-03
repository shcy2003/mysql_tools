"""
查询模块API路由配置
"""
from django.urls import path
from . import api_views

app_name = 'queries_api'

urlpatterns = [
    # 通用数据查询API - 支持分页、排序、筛选
    path('data/', api_views.api_query_data, name='api_query_data'),
]
