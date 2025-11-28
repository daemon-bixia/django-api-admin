from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import permissions

from django_api_admin.conf import app_settings


class IsAuthenticated(permissions.BasePermission):
    message = {
        "message": _("Authentication credentials were not provided."),
        "reason": "missing_credentials"
    }

    def has_permission(self, request, _view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminUser(permissions.BasePermission):

    message = {
        "message": _(
            "Staff permissions are required to access this resource"),
        "reason": "staff_only"
    }

    def has_permission(self, request, _view):
        return request.user.is_staff and request.user.is_active


class IsMFAEnabled(permissions.BasePermission):

    message = {
        "message": _("MFA is required to access this resource."),
        "reason": "mfa_required"
    }

    def has_permission(self, request, _view):
        from allauth.mfa.models import Authenticator

        if not request.user.is_authenticated:
            return False

        joined_ms = int(request.user.date_joined.timestamp() * 1000)
        now_ms = int(timezone.now().timestamp() * 1000)

        if now_ms - joined_ms < app_settings.MFA_SAFE_PERIOD:
            return True

        has_mfa = Authenticator.objects.filter(user=request.user).exists()

        return has_mfa
