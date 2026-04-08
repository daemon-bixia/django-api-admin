from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.utils.get_form_config import get_form_config
from django_api_admin.utils.get_inlines import get_inlines
from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples
from django_api_admin.serializers import FormFieldsSerializer
from django_api_admin.bulk import BulkOperation


class AddView(APIView):
    """
    Add new instances of this model. if this model has inline models associated with it 
    you can also add inline instances to this model.
    """
    serializer_class = None
    permission_classes = []
    model_admin = None

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "Successfully returned the field attributes list"),
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
        Handle GET requests to retrieve form field attributes and configuration
        for the model admin. 
        """
        data = dict()
        data['fields'] = self.model_admin.get_form_fields(request)
        data['config'] = get_form_config(self.model_admin)

        # Include the model_admin's inlines in the form representation
        if not self.model_admin.is_inline:
            inlines = get_inlines(request, self.model_admin)
            if len(inlines):
                data['inlines'] = inlines

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Handle POST requests to add a new instance of the model.
        """
        with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
            # If the user doesn't have add_permission respond with permission denied
            if not self.model_admin.has_add_permission(request):
                raise PermissionDenied

            # Initiate the serializer
            serializer = self.serializer_class(data=request.data.get('data', {}),
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
                    bulk_operation = BulkOperation(
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
