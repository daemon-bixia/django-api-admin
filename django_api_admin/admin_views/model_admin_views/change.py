from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ParseError, ValidationError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from django_api_admin.utils.quote import unquote
from django_api_admin.admins.model_admin import TO_FIELD_VAR
from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples, BulkUpdates
from django_api_admin.serializers import FormFieldsSerializer, BulkUpdatesResponseSerializer
from django_api_admin.bulk import InlineBulkOperation
from django_api_admin.utils.get_changed_data import get_changed_data
from django_api_admin.utils.flatten_fieldsets import flatten_fieldsets


class ChangeView(APIView):
    """
    Change an existing instance of this model. If the models has inline models associated with it, then
    create, update, and delete instances of the inline models as well.
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
    def get(self, request, object_id):
        obj = self.get_object(request, object_id)

        if not self.model_admin.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        if not self.model_admin.has_change_permission(request, obj):
            fieldsets = self.get_fieldsets(request, obj)
            readonly_fields = flatten_fieldsets(fieldsets)
            data = self.model_admin.get_form_description(
                request, obj, {"readonly_fields": readonly_fields})
        else:
            data = self.model_admin.get_form_description(request, obj)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "Successfully returned the field attributes list"),
                response=BulkUpdatesResponseSerializer,
                examples=[
                    OpenApiExample(
                        name=_("Update Success Response"),
                        summary=_(
                            "Example of a successful Update operation response"),
                        value=BulkUpdates,
                        status_codes=["200"]
                    )
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        },
    )
    def put(self, request, object_id):
        return self.update(request, object_id)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "Successfully returned the field attributes list"),
                response=BulkUpdatesResponseSerializer,
                examples=[
                    OpenApiExample(
                        name=_("Update Success Response"),
                        summary=_(
                            "Example of a successful Update operation response"),
                        value=BulkUpdates,
                        status_codes=["200"]
                    )
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        },
    )
    def patch(self, request, object_id):
        return self.update(request, object_id)

    def update(self, request, object_id):
        with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
            obj = self.get_object(request, object_id)

            # Test user change permission in this model.
            if not self.model_admin.has_change_permission(request, obj):
                raise PermissionDenied

            # Initiate the serializer based on the request method
            serializer = self.get_serializer_instance(request, obj)

            # Validate the update data
            if serializer.is_valid():
                changed_data = get_changed_data(serializer)
                updated_object = self.model_admin.save_serializer(
                    request, serializer, True)
                self.model_admin.save_model(
                    request, updated_object, serializer, True)

                # Process bulk operations
                inline_results = None
                bulk_operation = None
                if request.data.get("inlines"):
                    bulk_operation = InlineBulkOperation(
                        request, self.model_admin, updated_object, request.data.get("inlines"))

                    if bulk_operation.is_valid():
                        self.model_admin.save_related(
                            request, updated_object, serializer, bulk_operation, True)
                        inline_results = bulk_operation.result
                    else:
                        raise ValidationError(
                            {"errors": bulk_operation.errors})
                else:
                    serializer.save_m2m()

                # Construct the change message, and log the changes
                change_message = self.model_admin.construct_change_message(
                    request, (serializer, changed_data), inline_results, False)
                self.model_admin.log_change(
                    request, updated_object, change_message)

                return self.model_admin.response_change(request, updated_object, serializer, bulk_operation)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_instance(self, request, obj):
        serializer = None

        if request.method == 'PATCH':
            serializer = self.serializer_class(
                instance=obj, data=request.data.get('data', {}), partial=True, context={"request": request})

        elif request.method == 'PUT':
            serializer = self.serializer_class(
                instance=obj, data=request.data.get('data', {}), context={"request": request})

        elif request.method == 'GET':
            serializer = self.serializer_class(
                instance=obj, context={"request": request})

        return serializer

    def get_object(self, request, object_id):
        # Validate the reverse to field reference
        to_field = request.query_params.get(TO_FIELD_VAR)
        if to_field and not self.model_admin.to_field_allowed(request, to_field):
            raise ParseError(
                {'detail': _('The field %s cannot be referenced.') % to_field})

        obj = self.model_admin.get_object(
            request, unquote(object_id), to_field)

        # If the object doesn't exist respond with not found
        if obj is None:
            msg = _("%(name)s with ID “%(key)s” doesn't exist. Perhaps it was deleted?") % {
                'name': self.model_admin.model._meta.verbose_name,
                'key': unquote(object_id),
            }
            raise NotFound({'detail': msg})

        return obj
