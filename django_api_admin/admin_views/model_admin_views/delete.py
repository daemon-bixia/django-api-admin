from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.admins.model_admin import TO_FIELD_VAR
from django_api_admin.openapi import CommonAPIResponses, CommonAPIPathParams, CommonAPIQueryParams
from django_api_admin.serializers import ResponseMessageSerializer
from django_api_admin.utils.quote import unquote
from django_api_admin.mixins import APIAdminErrorViewMixin


class DeleteView(APIAdminErrorViewMixin, APIView):
    """
    Deletes a single instance of the model identified by the provided object ID,
    performing permission checks and handling related object cleanup.
    """

    serializer_class = ResponseMessageSerializer
    permission_classes = []
    model_admin = None
    admin_site = None

    @extend_schema(
        parameters=[CommonAPIPathParams.object_id, CommonAPIQueryParams.to_field],
        responses={
            204: OpenApiResponse(description=_("Successfully deleted the selected objects")),
            400: CommonAPIResponses.bad_request(_("_to_field value is not allowed")),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
            404: CommonAPIResponses.not_found(_("Model instance with the given id not found")),
            409: CommonAPIResponses.conflict(_("Cannot delete instance because it's protected")),
        },
    )
    def delete(self, request, object_id):
        with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
            opts = self.model_admin.model._meta

            # Validate the reverse to field reference.
            to_field = request.query_params.get(TO_FIELD_VAR)
            if to_field and not self.model_admin.to_field_allowed(request, to_field):
                raise ValidationError([{"message": "The field '%s' cannot be referenced." % to_field, "param": "_to_field"}])

            obj = self.model_admin.get_object(request, unquote(object_id), to_field)

            # Check delete object permission
            if not self.model_admin.has_delete_permission(request):
                raise PermissionDenied

            if obj is None:
                return Response({"status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            # Populate deleted_objects, a data structure of all related objects
            # that will also be deleted.
            (
                deleted_objects,
                model_count,
                perms_needed,
                protected,
            ) = self.model_admin.get_deleted_objects([obj], request)

            if not protected:
                if perms_needed:
                    raise PermissionDenied
                obj_display = str(obj)
                attr = str(to_field) if to_field else opts.pk.attname
                obj_id = obj.serializable_value(attr)
                self.model_admin.log_deletion(request, [obj])
                self.model_admin.delete_model(request, obj)

                return self.model_admin.response_delete(request, obj_display, obj_id)

            return Response({"status": 409}, status=status.HTTP_409_CONFLICT)
