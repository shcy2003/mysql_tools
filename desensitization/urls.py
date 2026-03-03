from django.urls import path
from . import views

app_name = 'desensitization'

urlpatterns = [
    path('', views.masking_rule_list_view, name='masking_rule_list'),
    path('create/', views.masking_rule_create_view, name='masking_rule_create'),
    path('edit/<int:rule_id>/', views.masking_rule_edit_view, name='masking_rule_edit'),
    path('delete/<int:rule_id>/', views.masking_rule_delete_view, name='masking_rule_delete'),
]