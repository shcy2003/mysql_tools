from django.urls import path
from . import views

app_name = 'queries'

urlpatterns = [
    path('', views.query_list_view, name='query_list'),
    # 统一使用新的SQL查询界面
    path('sql/', views.sql_query_new_view, name='sql_query'),
    # 保留旧路径的重定向，以便向后兼容
    path('sql/new/', views.sql_query_new_view, name='sql_query_new'),
    # Note: visual_query has been removed as per project requirements
    path('history/', views.query_history_view, name='query_history'),
    path('saved/', views.saved_queries_view, name='saved_queries'),
]