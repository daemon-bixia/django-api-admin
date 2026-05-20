from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.openapi import CommonAPIResponses


class PermissionsView(APIView):
    """
    Retrieve the permissions of the requesting user required to access the admin site.

    This endpoint dynamically evaluates the permission classes configured for the
    admin site against the current request and user context. It returns a mapping
    of each permission class name to a boolean value indicating whether the user
    satisfies the respective permission.
    """

    admin_site = None

    @extend_schema(
        operation_id="Retrieve user permissions",
        responses={
            200: OpenApiResponse(
                description=_("Map of user permission check results"),
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def get(self, request):
        permission_classes = self.admin_site.get_permission_classes(request)

        user_permissions = {}
        for permission_class in permission_classes:
            permission = permission_class()
            permission_name = permission.__class__.__name__
            try:
                has_permission = permission.has_permission(request, self)
            except PermissionDenied:
                has_permission = False
            except Exception:
                # In case a permission class raises an unexpected error
                has_permission = False
            user_permissions[permission_name] = has_permission

        serializer = self.get_serializer_class()(instance=user_permissions)
        return Response({"status": 200, "data": serializer.data}, status=200)

    def get_serializer_class(self):
        permission_classes = self.admin_site.get_permission_classes(None)
        fields = {
            permission_class.__name__: serializers.BooleanField(read_only=True)
            for permission_class in permission_classes
        }
        return type(
            "SitePermissionsSerializer", (serializers.Serializer,), fields)
