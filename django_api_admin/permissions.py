from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import permissions

from django_api_admin.conf import app_settings


class IsMFAEnabledOrGracePeriod(permissions.BasePermission):

    message = _("MFA is required to access this resource.")

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
