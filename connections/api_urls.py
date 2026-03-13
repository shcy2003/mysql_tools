"""
Connections API URL 配置
"""
from django.urls import path
from . import api_views

urlpatterns = [
    # 连接树 API
    path('tree/', api_views.api_connection_tree, name='api_connection_tree'),
    # 数据库列表 API
    path('<int:connection_id>/databases/', api_views.api_connection_databases, name='api_connection_databases'),
    # 表列表 API
    path('<int:connection_id>/tables/', api_views.api_connection_tables, name='api_connection_tables'),
    # 字段列表 API
    path('<int:connection_id>/columns/', api_views.api_connection_columns, name='api_connection_columns'),
    # 测试连接 API
    path('test/', api_views.api_test_connection, name='api_test_connection'),
]
