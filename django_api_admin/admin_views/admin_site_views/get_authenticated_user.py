from rest_framework.views import APIView
from django_api_admin.mixins import APIAdminErrorViewMixin


class AuthenticatedUserView(APIAdminErrorViewMixin, APIView):
    """
    Get the currently authenticated user
    """
