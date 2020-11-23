import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from hs_data_services_sync import tasks


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class UpdateServices(APIView):
    """
    """

    permission_classes = (IsAuthenticated|ReadOnly,)

    def post(self, request, resource_id, *args, **kwargs):
        """
        Checks HydroShare resource for data that can be exposed via WMS, WFS, WCS, or WOF web services,
        publishes those services, then returns access URLs to HydroShare.
        """

        response = {
            'success': True,
            'message': f'Update data services request received for resource: {resource_id}',
            'content': {}
        }

        tasks.update_data_services_task.delay(resource_id)

        return Response(response, status=status.HTTP_201_CREATED)


class GetServices(APIView):
    """
    """

    permission_classes = (IsAuthenticated|ReadOnly,)

    def get():
        return None
