from django.utils.translation import gettext_lazy as _

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from django_api_admin.serializers import AppIndexSerializer, AppSerializer
from django_api_admin.openapi import CommonAPIResponses


class AppIndexView(APIView):
    """
    Retrieve an app that has models registered in the admin site using `app_label`.
    """
    serializer_class = AppIndexSerializer
    permission_classes = []
    admin_site = None

    @extend_schema(
        operation_id="Get registered app details",
        parameters=[
            OpenApiParameter(
                name="app_label",
                type=str,
                location=OpenApiParameter.PATH,
                description=_("The label of the app to retrieve details for.")
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=AppSerializer,
                description=_("Application detail for the given `app_label`")
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
        return self.serializer_class(
            data={"app_label": app_label},
            context={'registered_app_labels': registered_app_labels}
        )
