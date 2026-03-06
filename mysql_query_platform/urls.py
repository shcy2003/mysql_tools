"""
MySQL Query Platform - Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger schema view configuration
schema_view = get_schema_view(
    openapi.Info(
        title="MySQL Query Platform API",
        default_version='v1',
        description="API Documentation for MySQL Query Platform",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

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
    path('api/', include('monitoring.urls')),

    # API Documentation
    path('api-doc/', include('apidoc.urls')),
]
