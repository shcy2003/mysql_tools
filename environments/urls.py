from django.urls import path
from . import views

app_name = 'environments'

urlpatterns = [
    path('', views.environment_list, name='environment_list'),
    path('create/', views.environment_create, name='environment_create'),
    path('edit/<int:env_id>/', views.environment_edit, name='environment_edit'),
    path('delete/<int:env_id>/', views.environment_delete, name='environment_delete'),
]
