from django.urls import path
from . import views

app_name = 'desensitization'

urlpatterns = [
    path('', views.masking_rule_list_view, name='masking_rule_list'),
    path('create/', views.masking_rule_create_view, name='masking_rule_create'),
    path('edit/<int:rule_id>/', views.masking_rule_edit_view, name='masking_rule_edit'),
    path('delete/<int:rule_id>/', views.masking_rule_delete_view, name='masking_rule_delete'),
    path('api/toggle/<int:rule_id>/', views.api_toggle_rule_status, name='api_toggle_rule_status'),
    path('api/check-column/', views.api_check_column_exists, name='api_check_column_exists'),
    path('api/test-rule/', views.api_test_masking_rule, name='api_test_masking_rule'),
]