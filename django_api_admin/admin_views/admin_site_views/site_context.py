from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.serializers import SiteContextSerializer
from django_api_admin.openapi import CommonAPIResponses
from django_api_admin.mixins import APIAdminErrorViewMixin


class SiteContextView(APIAdminErrorViewMixin, APIView):
    """
    Retrieve core attributes of the admin site.

    Returns a JSON payload containing configurable admin site settings such as
    `site_title`, `site_header`, `site_url`, and registered apps in the admin
    site.
    """

    permission_classes = []
    admin_site = None

    @extend_schema(
        operation_id="Retrieve admin site context",
        responses={
            200: OpenApiResponse(
                response=SiteContextSerializer,
                description=_("Retrieve site context attributes such as site title and header"),
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        },
    )
    def get(self, request):
        context = self.admin_site.each_context(request)
        return Response(context, status=status.HTTP_200_OK)
