from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from django_api_admin.serializers import AppListSerializer
from django_api_admin.openapi import CommonAPIResponses, OpenApiResponse


class AppListView(APIView):
    """
    Retrieve a list of all the apps that have models registered in the admin site.
    """
    permission_classes = []
    admin_site = None

    @extend_schema(
        operation_id="List registered applications",
        responses={
            200: OpenApiResponse(
                response=AppListSerializer,
                description=_("List of objects with application details")
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        },
    )
    def get(self, request):
        app_list = self.admin_site.get_app_list(request)
        return Response({"app_list": app_list}, status=status.HTTP_200_OK)
