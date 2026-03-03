from django.urls import path
from . import views

app_name = 'queries'

urlpatterns = [
    path('', views.query_list_view, name='query_list'),
    path('sql/', views.sql_query_view, name='sql_query'),
    path('sql/new/', views.sql_query_new_view, name='sql_query_new'),
    # Note: visual_query has been removed as per project requirements
    path('history/', views.query_history_view, name='query_history'),
]