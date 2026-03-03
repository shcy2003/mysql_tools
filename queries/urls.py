from django.urls import path
from . import views

app_name = 'queries'

urlpatterns = [
    path('', views.query_list_view, name='query_list'),
    path('sql/', views.sql_query_view, name='sql_query'),
    path('visual/', views.visual_query_view, name='visual_query'),
    path('history/', views.query_history_view, name='query_history'),
]