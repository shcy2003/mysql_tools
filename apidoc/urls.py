"""
API Documentation URLs
"""
from django.urls import path
from . import views

app_name = 'apidoc'

urlpatterns = [
    path('', views.api_doc_index, name='api_doc_index'),
]
