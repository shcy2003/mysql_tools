from django.urls import path
from . import views

app_name = 'connections'

urlpatterns = [
    path('', views.connection_list_view, name='connection_list'),
    path('create/', views.connection_create_view, name='connection_create'),
    path('edit/<int:connection_id>/', views.connection_edit_view, name='connection_edit'),
    path('delete/<int:connection_id>/', views.connection_delete_view, name='connection_delete'),
    path('test/<int:connection_id>/', views.connection_test_view, name='connection_test'),
]