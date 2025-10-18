from rest_framework.views import APIView


class AuthenticatedUserView(APIView):
    """
    Get the currently authenticated user
    """
