from django.utils.translation import gettext_lazy as _

from rest_framework import status, authentication
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication

from django_api_admin.openapi import User, CommonAPIResponses
from django_api_admin.serializers import UserSerializer


class UserInformation(APIView):
    serializer_class = None
    permission_classes = []
    authentication_classes = [
        authentication.SessionAuthentication,
        XSessionTokenAuthentication,
    ]
    admin_site = None

    @classmethod
    def as_view(cls, **initkwargs):
        if not len(initkwargs.get('authentication_classes', [])): 
            initkwargs['authentication_classes'] = cls.authentication_classes
        return super().as_view(**initkwargs)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_("Successful retrieval of user information"),
                response=UserSerializer,
                examples=[
                    OpenApiExample(
                        name=_("User Information"),
                        summary=_(
                            "Example of a successful user information retrieval response"),
                        description=_(
                            "Returns details of the user's information"),
                        value=User,
                        status_codes=["200"]
                    )
                ],
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response({'user': serializer.data})
