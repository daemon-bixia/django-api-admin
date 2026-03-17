from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ParseError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from django_api_admin.utils.quote import unquote
from django_api_admin.utils.diff_helper import ModelDiffHelper
from django_api_admin.utils.get_form_fields import get_form_fields
from django_api_admin.utils.get_form_config import get_form_config
from django_api_admin.utils.get_inlines import get_inlines
from django_api_admin.constants.vars import TO_FIELD_VAR
from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples, BulkUpdates
from django_api_admin.serializers import FormFieldsSerializer, BulkUpdatesResponseSerializer
from django_api_admin.bulk import BulkOperations


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
        # Initiate the serializer based on the request method
        serializer = self.get_serializer_instance(request, obj)
        data = dict()
        data['fields'] = get_form_fields(serializer, change=True)
        data['config'] = get_form_config(self.model_admin)

        # Include the model_admin's inlines in the form representation
        if not self.model_admin.is_inline:
            inlines = get_inlines(request, self.model_admin, obj=obj)
            if inlines:
                data['inlines'] = inlines

        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, object_id):
        with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
            obj = self.get_object(request, object_id)
            opts = self.model_admin.model._meta
            helper = ModelDiffHelper(obj)

            # Test user change permission in this model.
            if not self.model_admin.has_change_permission(request):
                raise PermissionDenied

            # Initiate the serializer based on the request method
            serializer = self.get_serializer_instance(request, obj)

            # Update and log the changes to the object
            if serializer.is_valid():
                updated_object = serializer.save()

                msg = _(
                    f'The {opts.verbose_name} “{str(updated_object)}” was changed successfully.')
                data = {'data': serializer.data, 'detail': msg}

                # Log the change of  change
                self.model_admin.log_change(request, updated_object, [{'changed': {
                    'name': str(updated_object._meta.verbose_name),
                    'object': str(updated_object),
                    'fields': helper.set_changed_model(updated_object).changed_fields
                }}])

                # Process bulk operations
                if request.data.get("inlines"):
                    operation = BulkOperations(
                        request, self.model_admin, obj, request.data.get("inlines"))

                    if operation.is_valid():
                        operation.save()

                        data["inlines"] = {}
                        if operation.added:
                            data["inlines"]["added"] = operation.added
                        if operation.changed:
                            data["inlines"]["changed"] = operation.changed
                        if operation.deleted:
                            data["inlines"]["deleted"] = operation.deleted

                return Response(data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    def get_serializer_instance(self, request, obj):
        serializer = None

        if request.method == 'PATCH':
            serializer = self.serializer_class(
                instance=obj, data=request.data.get('data', {}), partial=True)

        elif request.method == 'PUT':
            serializer = self.serializer_class(
                instance=obj, data=request.data.get('data', {}))

        elif request.method == 'GET':
            serializer = self.serializer_class(instance=obj)

        return serializer

    def get_object(self, request, object_id):
        # Validate the reverse to field reference
        to_field = request.query_params.get(TO_FIELD_VAR)
        if to_field and not self.model_admin.to_field_allowed(to_field):
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
