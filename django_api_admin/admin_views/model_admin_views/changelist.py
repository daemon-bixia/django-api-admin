from django.db.models import Model
from django.db import router, transaction
from django.utils.translation import gettext_lazy as _, ngettext
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from django_api_admin.utils.label_for_field import label_for_field
from django_api_admin.utils.lookup_field import lookup_field
from django_api_admin.exceptions import IncorrectLookupParameters
from django_api_admin.serializers import ChangeListSerializer, ChangelistResponseSerializer
from django_api_admin.openapi import CommonAPIResponses, ChangeList
from django_api_admin.bulk import ChangelistBulkOperation
from django_api_admin.utils.model_ngettext import model_ngettext


class ChangeListView(APIView):
    """
    Return a JSON object representing the django admin changelist table.
    supports querystring filtering, pagination and search also changes based on list display.
    """
    serializer_class = None
    permission_classes = []
    model_admin = None

    @extend_schema(
        parameters=[ChangeListSerializer],
        responses={
            200: OpenApiResponse(
                description=_(
                    "Retrieve a list of records with optional filtering and pagination"),
                response=ChangelistResponseSerializer,
                examples=[OpenApiExample(
                    name=_("Success Response"),
                    summary=_("Example of a successful changelist retrieval"),
                    description=_(
                        "Returns a paginated list of records with optional filters applied."),
                    value=ChangeList,
                    status_codes=["200"],
                )]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        }
    )
    def get(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        try:
            cl = self.model_admin.get_changelist_instance(request)
        except IncorrectLookupParameters as e:
            raise ValidationError(str(e))

        columns = self.get_columns(request, cl)
        rows = self.get_rows(request, cl)
        config = self.get_config(request, cl)
        return Response({'config': config, 'columns': columns, 'rows': rows},
                        status=status.HTTP_200_OK)

    def put(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied
        serializer_class = self.model_admin.get_changelist_serializer_class(
            request)
        modified_objects = self.model_admin._get_list_editable_queryset()
        cl.bulk_operation = ChangelistBulkOperation(
            request, self.model_admin, modified_objects, request.data.get('data', {}), serializer_class)
        if cl.bulk_operation.is_valid():
            changecount = 0
            with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
                for serializer, changed_data in cl.bulk_operation.result.values():
                    if changed_data:
                        updated_object = self.model_admin.save_serializer(
                            request, serializer, changed=True)
                        self.model_admin.save_model(
                            request, updated_object, serializer, change=True)
                        serializer.save_m2m()
                        change_message = self.model_admin.construct_change_message(
                            request, (serializer, changed_data), None, False)
                        self.model_admin.log_change(
                            request, updated_object, change_message)
                        changecount += 1
            if changecount:
                msg = ngettext(
                    "%(count)s %(name)s was changed successfully.",
                    "%(count)s %(name)s were changed successfully.",
                    changecount,
                ) % {
                    "count": changecount,
                    "name": model_ngettext(self.opts, changecount),
                }

            return Response({
                "detail": msg,
                "data": cl.bulk_operation.validated_data
            }, status=status.HTTP_200_OK)

        raise ValidationError({"errors": cl.bulk_operation.errors})

    def get_columns(self, request, cl):
        """
        return changelist columns or headers.
        """
        columns = []
        for field_name in self.get_fields_list(request, cl):
            text, _ = label_for_field(
                field_name, cl.model, model_admin=cl.model_admin, return_attr=True)
            columns.append({'field': field_name, 'headerName': text})
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
            model_info = (cl.model_admin.admin_site.name, type(
                result)._meta.app_label, type(result)._meta.model_name)
            row = {
                'change_url': reverse('%s:%s_%s_change' % model_info, kwargs={'object_id': result.pk}, request=request),
                'id': result.pk,
                'cells': {}
            }

            # Construct the `cells` dictionary
            for field_name in self.get_fields_list(request, cl):
                try:
                    # Get the field value
                    _, _, value = lookup_field(
                        field_name, result, cl.model_admin)

                    # If the value is a Model instance get the string representation
                    if value and isinstance(value, Model):
                        result_repr = str(value)
                    else:
                        result_repr = value

                    # If there are choices display the choice description string instead of the value
                    try:
                        model_field = result._meta.get_field(field_name)
                        choices = getattr(model_field, 'choices', None)
                        if choices:
                            repr_list = [
                                choice for choice in choices if choice[0] == value]
                            result_repr = repr_list[0][1] if len(
                                repr_list) > 1 else str(value)
                    except FieldDoesNotExist:
                        pass

                    # If the value is null set result_repr to empty_value_display
                    if value is None:
                        result_repr = empty_value_display

                    # If the `field_name` is in `cl.list_editable` use the form fields description
                    if field_name in cl.list_editable:
                        fields_description = self.model_admin.get_changelist_form_fields_description(
                            request, result)
                        for field_description in fields_description:
                            if field_description["name"] == field_name:
                                result_repr = field_description

                except ObjectDoesNotExist:
                    result_repr = empty_value_display

                row['cells'][field_name] = result_repr
            rows.append(row)
        return rows

    def get_config(self, request, cl):
        config = {}

        # Add the ModelAdmin attributes that the changelist uses
        for option_name in cl.model_admin.changelist_options:
            config[option_name] = (getattr(cl.model_admin, option_name, None))

        # Changelist pagination attributes
        config['full_count'] = cl.full_result_count
        config['result_count'] = cl.result_count

        # A list of action names and choices
        config['action_choices'] = cl.model_admin.get_action_choices(
            request, [])

        # A list of filters titles and choices
        filters_spec, _, _, _, _ = cl.get_filters(request)
        if filters_spec:
            config['filters'] = [
                {"title": filter.title, "choices": filter.choices(cl)} for filter in filters_spec]
        else:
            config['filters'] = []

        # A list of fields that you can sort with
        list_display_fields = []
        for field_name in self.get_fields_list(request, cl):
            try:
                cl.model._meta.get_field(field_name)
                list_display_fields.append(field_name)
            except FieldDoesNotExist:
                pass
        config['list_display_fields'] = list_display_fields

        return config

    def get_fields_list(self, request, cl):
        list_display = cl.model_admin.list_display
        exclude = cl.model_admin.exclude or tuple()
        fields_list = tuple(
            filter(lambda item: item not in exclude, list_display))
        return fields_list
