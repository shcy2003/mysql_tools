"""
MySQL Query Platform - Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 根路径重定向到查询列表
    path('', RedirectView.as_view(pattern_name='queries:query_list', permanent=False)),
    
    # Web Views
    path('accounts/', include('accounts.urls')),
    path('connections/', include('connections.urls')),
    path('queries/', include('queries.urls')),
    path('audit/', include('audit.urls')),
    path('desensitization/', include('desensitization.urls')),
    
    # API Endpoints
    path('api/connections/', include('connections.api_urls')),
    path('api/queries/', include('queries.api_urls')),
]
