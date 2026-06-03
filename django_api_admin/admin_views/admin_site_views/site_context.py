from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from django_api_admin.serializers import SiteContextSerializer
from django_api_admin.openapi import CommonAPIResponses


class SiteContextView(APIView):
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
                examples=[
                    OpenApiExample(
                        name=_("Success Response"),
                        value={
                            "site_title": "Django site admin",
                            "site_header": "Django administration",
                            "site_url": "/",
                            "has_permission": True,
                            "available_apps": [
                                {
                                    "name": "Authentication and Authorization",
                                    "app_label": "auth",
                                    "app_url": "/api_admin/auth/",
                                    "has_module_perms": True,
                                    "models": [
                                        {
                                            "name": "Users",
                                            "object_name": "User",
                                            "perms": {"add": True, "change": True, "delete": True, "view": True},
                                        }
                                    ],
                                }
                            ],
                            "is_nav_sidebar_enabled": True,
                        },
                        status_codes=["200"],
                    )
                ],
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        },
    )
    def get(self, request):
        context = self.admin_site.each_context(request)
        return Response(context, status=status.HTTP_200_OK)
