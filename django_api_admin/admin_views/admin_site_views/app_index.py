from django.utils.translation import gettext_lazy as _

from rest_framework.response import Response
from rest_framework import status, authentication
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication

from django_api_admin.serializers import AppIndexSerializer, AppSerializer
from django_api_admin.openapi import CommonAPIResponses


class AppIndexView(APIView):
    """
    Lists models inside a given app.
    """
    serializer_class = AppIndexSerializer
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
        operation_id="app_index",
        request=AppIndexSerializer,
        responses={
            200: OpenApiResponse(
                response=AppSerializer,
                description=_(
                    "Successfully constructed the list of registered models")
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def get(self, request, app_label):
        serializer = self.get_serializer(app_label)
        if not serializer.is_valid():
            raise ParseError({"detail": _("invalid app_label")})

        app_dict = self.admin_site._build_app_dict(request, app_label)

        if not app_dict:
            return Response({'detail': _('The requested admin page does not exist.')},
                            status=status.HTTP_404_NOT_FOUND)

        # Sort the models alphabetically within each app.
        app_dict['models'].sort(key=lambda x: x['name'])

        data = {
            'app_label': app_label,
            'app': app_dict,
        }
        return Response(data, status=status.HTTP_200_OK)

    def get_serializer(self, app_label):
        registered_app_labels = {
            model._meta.app_label for model in self.admin_site._registry.keys()
        }
        return AppIndexSerializer(
            data={"app_label": app_label},
            context={'registered_app_labels': registered_app_labels}
        )
