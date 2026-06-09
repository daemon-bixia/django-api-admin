from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import (
    PermissionDenied,
    NotFound,
    ParseError,
    ValidationError,
)
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.utils.quote import unquote
from django_api_admin.admins.model_admin import TO_FIELD_VAR
from django_api_admin.openapi import (
    CommonAPIResponses,
    CommonAPIPathParams,
    APIResponseExamples,
    CommonAPIQueryParams,
)
from django_api_admin.serializers import (
    FormFieldsResponseSerializer,
    ChangeViewErrorResponseSerializer,
)
from django_api_admin.mixins import APIAdminErrorViewMixin
from django_api_admin.bulk import InlineBulkOperation
from django_api_admin.utils.get_changed_data import get_changed_data
from django_api_admin.utils.flatten_fieldsets import flatten_fieldsets
from django_api_admin.utils.format_error import format_error


class ChangeView(APIAdminErrorViewMixin, APIView):
    """
    Update an instance of this model identified by its object_id.

    This endpoint supports partial updates. It also allows you to update
    related child instances simultaneously, provided their models are configured
    as Inlines in the ModelAdmin.
    """

    serializer_class = None
    permission_classes = []
    model_admin = None
    admin_site = None

    @extend_schema(
        parameters=[CommonAPIPathParams.object_id, CommonAPIQueryParams.to_field],
        responses={
            200: OpenApiResponse(
                description=_("Configurations and a list of fields representing the change form"),
                response=FormFieldsResponseSerializer,
                examples=[APIResponseExamples.form_description()],
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        },
    )
    def get(self, request, object_id):
        """
        Retrieve the configurations required to construct the change form and inline forms
        on the client.

        This includes serializer field attributes, permissions, form styles, the location
        of the save button, names of fields utilizing custom widgets (e.g., `filter_horizontal`),
        and any custom values added by overriding `ModelAdmin.get_form_description()`
        """
        obj = self.get_object(request, object_id)

        if not self.model_admin.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        if not self.model_admin.has_change_permission(request, obj):
            fieldsets = self.get_fieldsets(request, obj)
            readonly_fields = flatten_fieldsets(fieldsets)
            data = self.model_admin.get_form_description(request, obj, {"readonly_fields": readonly_fields})
        else:
            data = self.model_admin.get_form_description(request, obj)

        return Response({"status": status.HTTP_200_OK, "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[CommonAPIPathParams.object_id],
        responses={
            200: OpenApiResponse(
                description=_("The serialized instance, and inlines that were affected"),
            ),
            400: OpenApiResponse(
                description=_("Failed to add records"),
                response=ChangeViewErrorResponseSerializer,
            ),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
        },
    )
    def patch(self, request, object_id):
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
                updated_object = self.model_admin.save_serializer(request, serializer, True)
                self.model_admin.save_model(request, updated_object, serializer, True)

                # Process bulk operations
                inline_results = None
                bulk_operation = None
                if request.data.get("inlines"):
                    bulk_operation = InlineBulkOperation(
                        request,
                        self.model_admin,
                        updated_object,
                        request.data.get("inlines"),
                    )
                    if bulk_operation.is_valid():
                        self.model_admin.save_related(request, updated_object, serializer, bulk_operation, True)
                        inline_results = bulk_operation.result
                    else:
                        raise ValidationError({"inlines": bulk_operation.errors})
                else:
                    serializer.save_m2m()

                # Construct the change message, and log the changes
                change_message = self.model_admin.construct_change_message(
                    request, (serializer, changed_data), inline_results, False
                )
                self.model_admin.log_change(request, updated_object, change_message)

                return self.model_admin.response_change(request, updated_object, serializer, bulk_operation)

            raise ValidationError({"form": format_error(serializer.errors)})

    def get_serializer_instance(self, request, obj):
        serializer = None

        if request.method == "PATCH":
            serializer = self.serializer_class(
                instance=obj,
                data=request.data.get("data", {}),
                partial=True,
                context={"request": request},
            )

        elif request.method == "PUT":
            serializer = self.serializer_class(
                instance=obj,
                data=request.data.get("data", {}),
                context={"request": request},
            )

        elif request.method == "GET":
            serializer = self.serializer_class(instance=obj, context={"request": request})

        return serializer

    def get_object(self, request, object_id):
        # Validate the reverse to field reference
        to_field = request.query_params.get(TO_FIELD_VAR)
        if to_field and not self.model_admin.to_field_allowed(request, to_field):
            raise ParseError({"detail": _("The field %s cannot be referenced.") % to_field})

        obj = self.model_admin.get_object(request, unquote(object_id), to_field)

        # If the object doesn't exist respond with not found
        if obj is None:
            msg = _("%(name)s with ID “%(key)s” doesn't exist. Perhaps it was deleted?") % {
                "name": self.model_admin.model._meta.verbose_name,
                "key": unquote(object_id),
            }
            raise NotFound({"detail": msg})

        return obj
