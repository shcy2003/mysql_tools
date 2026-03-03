"""
Connections API URL 配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # 连接树 API
    path('tree/', views.api_connection_tree, name='api_connection_tree'),
    # 数据库列表 API
    path('<int:connection_id>/databases/', views.api_connection_databases, name='api_connection_databases'),
    # 表列表 API
    path('<int:connection_id>/tables/', views.api_connection_tables, name='api_connection_tables'),
]
