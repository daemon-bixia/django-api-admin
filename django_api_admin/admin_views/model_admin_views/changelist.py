from django.db.models import Model
from django.db import router, transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.mixins import APIAdminErrorViewMixin
from django_api_admin.exceptions import IncorrectLookupParameters
from django_api_admin.serializers import ChangeListSerializer, ChangelistResponseSerializer, ChangelistErrorResponseSerializer
from django_api_admin.openapi import CommonAPIResponses
from django_api_admin.bulk import ChangelistBulkOperation
from django_api_admin.utils.get_form_fields import get_form_fields_description
from django_api_admin.utils.label_for_field import label_for_field
from django_api_admin.utils.lookup_field import lookup_field


class ChangelistView(APIAdminErrorViewMixin, APIView):
    serializer_class = None
    permission_classes = []
    model_admin = None
    admin_site = None

    @extend_schema(
        parameters=[ChangeListSerializer],
        responses={
            200: OpenApiResponse(
                description=_("Column definitions, and row data"),
                response=ChangelistResponseSerializer,
            ),
            400: CommonAPIResponses.bad_request(),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
        },
    )
    def get(self, request):
        """
        Retrieve the changelist data.

        Returns a JSON response containing column definitions, row data,
        and configuration for filters and actions.
        """
        if not self.model_admin.has_view_or_change_permission(request):
            raise PermissionDenied

        cl = self.get_changelist_instance(request)
        columns = self.get_columns(request, cl)
        rows = self.get_rows(request, cl)
        config = self.get_config(request, cl)

        serializer_class = self.get_action_serializer_class(request)
        serializer = serializer_class(context={"request": request})
        action_form = get_form_fields_description(serializer, self.model_admin, change=False)

        data = {
            "status": status.HTTP_200_OK,
            "data": {"columns": columns, "rows": rows, "config": config, "action_form": action_form},
        }

        if cl.list_editable:
            list_editing_formset = self.get_list_editing_formset(request, cl)
            data["data"]["list_editing_formset"] = list_editing_formset

        return Response(
            data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={
            200: CommonAPIResponses.ok("Action was executed on selected objects"),
            400: CommonAPIResponses.bad_request(),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
        }
    )
    def post(self, request):
        """
        Execute administrative actions on changelist records.

        Performs the selected action on the chosen set of records.
        """
        cl = self.get_changelist_instance(request)
        queryset = cl.get_queryset(request)
        return self.model_admin.response_action(request, queryset)

    @extend_schema(
        responses={
            200: OpenApiResponse(description=_("Records were updated successfully")),
            400: OpenApiResponse(
                description=_("Failed to update records"),
                response=ChangelistErrorResponseSerializer,
            ),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
        }
    )
    def put(self, request):
        """
        Perform bulk updates on changelist records.

        Updates multiple records at once for fields marked as 'list_editable'.
        """
        cl = self.get_changelist_instance(request)
        if not self.model_admin.has_change_permission(request):
            raise PermissionDenied
        serializer_class = self.model_admin.get_changelist_serializer_class(request)
        # Ensure that all items have a pk field
        errors = {}
        for idx, item in enumerate(request.data.get("data", [])):
            if "pk" not in item:
                errors[idx] = [{"message": "This field is required.", "param": "pk"}]
        if errors:
            raise ValidationError(errors)
        modified_objects = self.model_admin._get_list_editable_queryset(request)
        cl.bulk_operation = ChangelistBulkOperation(
            request, self.model_admin, modified_objects, request.data.get("data", {}), serializer_class
        )
        if cl.bulk_operation.is_valid():
            with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
                for serializer, changed_data in cl.bulk_operation.result.values():
                    if changed_data:
                        updated_object = self.model_admin.save_serializer(request, serializer, change=True)
                        self.model_admin.save_model(request, updated_object, serializer, change=True)
                        serializer.save_m2m()
                        change_message = self.model_admin.construct_change_message(
                            request, (serializer, changed_data), None, False
                        )
                        self.model_admin.log_change(request, updated_object, change_message)

            return Response(
                {"status": status.HTTP_200_OK, "data": cl.bulk_operation.validated_data},
                status=status.HTTP_200_OK,
            )

        raise ValidationError(cl.bulk_operation.errors)

    def get_columns(self, request, cl):
        """
        Return changelist columns or headers.
        """
        columns = []
        for field_name in self.get_fields_list(request, cl):
            text, _ = label_for_field(field_name, cl.model, model_admin=cl.model_admin, return_attr=True)
            columns.append({"field": field_name, "headerName": text})
        return columns

    def get_rows(self, request, cl):
        """
        Return changelist rows actual list of data.
        """
        rows = []
        # Generate changelist attributes (e.g result_list, paginator, result_count)
        cl.get_results(request)
        empty_value_display = cl.model_admin.get_empty_value_display()
        for result in cl.result_list:
            row = {"id": result.pk, "cells": {}}

            # Construct the `cells` dictionary
            for field_name in self.get_fields_list(request, cl):
                try:
                    # Get the field value
                    _, _, value = lookup_field(field_name, result, cl.model_admin)

                    # If the value is a Model instance get the string representation
                    if value and isinstance(value, Model):
                        result_repr = str(value)
                    else:
                        result_repr = value

                    # If there are choices display the choice description string instead of the value
                    try:
                        model_field = result._meta.get_field(field_name)
                        choices = getattr(model_field, "choices", None)
                        if choices:
                            repr_list = [choice for choice in choices if choice[0] == value]
                            result_repr = repr_list[0][1] if len(repr_list) > 1 else str(value)
                    except FieldDoesNotExist:
                        pass

                    # If the value is null set result_repr to empty_value_display
                    if value is None:
                        result_repr = empty_value_display
                except ObjectDoesNotExist:
                    result_repr = empty_value_display

                row["cells"][field_name] = result_repr
            rows.append(row)
        return rows

    def get_config(self, request, cl):
        config = {}

        # Add the ModelAdmin attributes that the changelist uses
        for option_name in cl.model_admin.changelist_options:
            config[option_name] = getattr(cl.model_admin, option_name, None)

        # Changelist pagination attributes
        config["full_count"] = cl.full_result_count
        config["result_count"] = cl.result_count

        # A list of action names and choices
        config["action_choices"] = cl.model_admin.get_action_choices(request, [])

        # A list of filters titles and choices
        filter_specs, _, _, _, _ = cl.get_filters(request)
        if filter_specs:
            config["filters"] = [
                {
                    "title": s.title,
                    "choices": list(s.choices(cl)),
                }
                for s in filter_specs
            ]
        else:
            config["filters"] = []

        # A list of fields that you can sort with
        list_display_fields = []
        for field_name in self.get_fields_list(request, cl):
            try:
                cl.model._meta.get_field(field_name)
                list_display_fields.append(field_name)
            except FieldDoesNotExist:
                pass
        config["list_display_fields"] = list_display_fields

        # Include the active column ordering
        config["ordering_field_columns"] = cl.get_ordering_field_columns()

        return config

    def get_list_editing_formset(self, request, cl):
        # A list of form field descriptions you can use to build the list-editable form
        formset = []
        for result in cl.result_list:
            fields = []
            field_descriptions = self.model_admin.get_changelist_form_fields_description(request, result)
            for field_name in cl.list_editable:
                for field_description in field_descriptions:
                    if field_description["name"] == field_name:
                        fields.append(field_description)
            formset.append(fields)
        return formset

    def get_fields_list(self, request, cl):
        list_display = cl.model_admin.list_display
        exclude = cl.model_admin.exclude or tuple()
        fields_list = tuple(filter(lambda item: item not in exclude, list_display))
        return fields_list

    def get_changelist_instance(self, request):
        try:
            return self.model_admin.get_changelist_instance(request)
        except IncorrectLookupParameters as e:
            raise ValidationError([{"message": [str(e)], "param": "non_field_errors"}])

    def get_action_serializer_class(self, request):
        return self.model_admin.get_action_serializer_class(request)
