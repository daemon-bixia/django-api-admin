from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from django_api_admin.exceptions import IncorrectLookupParameters
from django_api_admin.utils.get_form_fields import get_form_fields_description
from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples
from django_api_admin.serializers import FormFieldsSerializer


class HandleActionView(APIView):
    """
    Preform admin actions on objects using json.
    """
    permission_classes = []
    model_admin = None

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Successfully returned the field attributes list",
                response=FormFieldsSerializer,
                examples=[
                    APIResponseExamples.field_attributes()
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        },
    )
    def get(self, request):
        """
        Handle GET requests to retrieve a list of form field attributes for
        the admin action.
        """
        serializer = self.get_serializer_class(request)()
        form_fields = get_form_fields_description(serializer)
        return Response({'fields': form_fields}, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "Action executed successfully on selected objects"),
                response=dict,
                examples=[
                    OpenApiExample(
                        name=_("Success Response"),
                        summary=_("Example of a successful action execution"),
                        description=_(
                            "Returns a success message after performing the selected action on chosen objects"),
                        value={"detail": "action was performed successfully"},
                        status_codes=["200"]
                    )
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def post(self, request):
        try:
            cl = self.model_admin.get_changelist_instance(request)
        except IncorrectLookupParameters as e:
            raise NotFound(str(e))

        queryset = cl.get_queryset(request)
        return self.model_admin.response_action(request, queryset)

    def get_serializer_class(self):
        return self.model_admin.get_action_serializer_class(self.request)
