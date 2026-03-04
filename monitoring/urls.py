"""
Monitoring API URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Database health endpoints
    path('health/', views.all_health_check, name='all_health'),
    path('health/db/', views.db_health_check, name='db_health'),
    path('health/db/stats/', views.db_health_stats, name='db_health_stats'),
]
