from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import permissions

from django_api_admin.conf import app_settings


class IsStaffUser(permissions.BasePermission):

    message = _("Staff permissions are required to access this resource")

    def has_permission(self, request):
        if not request.user.is_authenticated:
            return False

        return request.user.is_staff and request.user.is_active


class IsMFAEnabled(permissions.BasePermission):

    message = _("MFA is required to access this resource")

    def has_permission(self, request):
        from allauth.mfa.models import Authenticator

        joined_ms = int(request.user.date_joined.timestamp() * 1000)
        now_ms = int(timezone.now().timestamp() * 1000)

        if now_ms - joined_ms < app_settings.MFA_SAFE_PERIOD:
            return True

        return Authenticator.objects.filter(user=request.user).exists()
