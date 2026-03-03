"""
连接模块API路由配置
"""
from django.urls import path
from . import api_views

app_name = 'connections_api'

urlpatterns = [
    # 获取连接树
    path('tree/', api_views.api_connection_tree, name='api_connection_tree'),
    # 获取数据库列表
    path('<int:connection_id>/databases/', api_views.api_connection_databases, name='api_connection_databases'),
    # 获取表列表
    path('<int:connection_id>/tables/', api_views.api_connection_tables, name='api_connection_tables'),
]
