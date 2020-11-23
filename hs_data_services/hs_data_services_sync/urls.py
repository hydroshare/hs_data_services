from django.urls import path
from hs_data_services_sync import views


urlpatterns = [
    path('update/<str:resource_id>/', views.UpdateServices.as_view(), name='post_update_services'),
    path('verify/', views.GetServices.as_view(), name='get_services'),
]
