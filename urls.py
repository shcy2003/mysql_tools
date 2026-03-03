"""
MySQL Query Platform - Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Web Views
    path('', include('accounts.urls')),
    path('connections/', include('connections.urls')),
    path('queries/', include('queries.urls')),
    path('audit/', include('audit.urls')),
    path('desensitization/', include('desensitization.urls')),
    
    # API Endpoints
    path('api/connections/', include('connections.api_urls')),
    path('api/queries/', include('queries.api_urls')),
]
