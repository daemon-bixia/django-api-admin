from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.utils.get_form_fields import get_form_fields
from django_api_admin.utils.get_form_config import get_form_config
from django_api_admin.utils.validate_bulk_edits import validate_bulk_edits
from django_api_admin.utils.get_inlines import get_inlines
from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples
from django_api_admin.serializers import FormFieldsSerializer


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
        serializer = self.serializer_class()
        data['fields'] = get_form_fields(serializer)
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

            # Validate the new_object data
            serializer = self.serializer_class(
                data=request.data.get('data', {}))
            if serializer.is_valid():
                # Create the `data` object in the request body used to create the new_object
                opts = self.model_admin.model._meta
                new_object = serializer.save()
                msg = _(
                    f'The {opts.verbose_name} “{str(new_object)}” was added successfully.')

                # Log addition of the new instance
                self.model_admin.log_addition(request, new_object, [{'added': {
                    'name': str(new_object._meta.verbose_name),
                    'object': str(new_object),
                }}])

                # Process inline bulk additions
                created_inlines = []
                if request.data.get("create_inlines", None):
                    # Validate the create_inlines data
                    valid_serializers = validate_bulk_edits(
                        request, self.model_admin, new_object)
                    # Save the inline data (inside a transaction).
                    for inline_serializer in valid_serializers:
                        inline_serializer.save()
                    # Return the data to the user.
                    created_inlines = [
                        inline_serializer.data for inline_serializer in valid_serializers]

                # Return the appropriate 201 response based on the data
                data = {'data': serializer.data, 'detail': msg}
                if len(created_inlines):
                    data['created_inlines'] = created_inlines

                return Response(data, status=status.HTTP_201_CREATED)

            # return a 400 response indicating failure
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
