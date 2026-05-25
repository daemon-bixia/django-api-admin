from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples
from django_api_admin.serializers import FormFieldsSerializer
from django_api_admin.bulk import InlineBulkOperation


class AddView(APIView):
    """
    Create a new instance of this model.

    This endpoint supports creating the main model instance along with its
    related child instances simultaneously, provided their models are configured
    as Inlines in the ModelAdmin.
    """
    serializer_class = None
    permission_classes = []
    model_admin = None

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "Configurations and a list of fields representing the add form"),
                response=FormFieldsSerializer,
                examples=[APIResponseExamples.form_description()]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        },
    )
    def get(self, request):
        """
        Retrieve the configurations required to construct the add form and inline forms
        on the client.

        This includes serializer field attributes, permissions, form styles, the location
        of the save button, names of fields utilizing custom widgets (e.g., `filter_horizontal`),
        and any custom values added by overriding `ModelAdmin.get_form_description()`
        """
        if not self.model_admin.has_add_permission(request):
            raise PermissionDenied
        data = self.model_admin.get_form_description(request, obj=None)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "The serialized instance, and inlines that were affected")
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        },
    )
    def post(self, request):
        with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
            # If the user doesn't have add_permission respond with permission denied
            if not self.model_admin.has_add_permission(request):
                raise PermissionDenied

            # Initiate the serializer
            serializer = self.serializer_class(data=request.data.get("data", {}),
                                               context={"request": request})

            # Validate the new_object data
            if serializer.is_valid():
                new_object = self.model_admin.save_serializer(
                    request, serializer, False)
                self.model_admin.save_model(
                    request, new_object, serializer, False)

                # Process bulk operations
                inline_results = None
                bulk_operation = None
                if request.data.get("inlines"):
                    bulk_operation = InlineBulkOperation(
                        request, self.model_admin, new_object, request.data.get("inlines"))

                    if bulk_operation.is_valid():
                        self.model_admin.save_related(
                            request, new_object, serializer, bulk_operation, False)
                        inline_results = bulk_operation.result
                    else:
                        raise ValidationError(
                            {"errors": bulk_operation.errors})
                else:
                    serializer.save_m2m()

                # Construct the change message, and log the changes
                change_message = self.model_admin.construct_change_message(
                    request, (serializer, []), inline_results, False)
                self.model_admin.log_change(
                    request, new_object, change_message)

                return self.model_admin.response_add(request, new_object, serializer, bulk_operation)

            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
