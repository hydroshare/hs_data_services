from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from hs_data_services import settings


schema_view = get_schema_view(
   openapi.Info(
      title="HydroShare Data Services API",
      default_version='v1.0',
      description="HydroShare Data Services Rest API",
      contact=openapi.Contact(email="kjlippold@gmail.com")
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url=settings.PROXY_BASE_URL
)

urlpatterns = [
    path('his/admin/', admin.site.urls),
    path('his/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('his/services/', include('hs_data_services_sync.urls')),
]
