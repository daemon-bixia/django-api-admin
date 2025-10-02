from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied


class PermissionsView(APIView):
    """
    Returns the permissions required by the user to access the admin panel
    """
    admin_site = None

    def get(self, request):
        # Check if the use has staff permissions
        if not request.user.is_staff:
            raise PermissionDenied({
                "message": _("Staff permissions are required to access this resource"),
                "meta": "staff_only"
            })

        permission_classes = self.admin_site.get_permission_classes()

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
        return Response(serializer.data)

    def get_serializer_class(self):
        """
        Not required used only for OpenAPI schema generation
        """
        permission_classes = self.admin_site.get_permission_classes()
        fields = {
            permission_class.__name__: serializers.BooleanField(read_only=True)
            for permission_class in permission_classes
        }
        return type('SitePermissionsSerializer', (serializers.Serializer,), fields)
