from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from django_api_admin.utils.quote import unquote
from django_api_admin.admins.model_admin import TO_FIELD_VAR
from django_api_admin.openapi import CommonAPIResponses
from django_api_admin.serializers import ResponseMessageSerializer


class DeleteView(APIView):
    """
    Delete a single object from this model
    """
    serializer_class = ResponseMessageSerializer
    permission_classes = []
    model_admin = None

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_("Successfully deleted the selected objects"),
                response=dict,
                examples=[
                    OpenApiExample(
                        name=_("Delete Success Response"),
                        summary=_("Example of a successful delete operation"),
                        description=_(
                            "Returns a success message after deleting the selected objects"),
                        value={
                            "detail": "The object was deleted successfully."
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def delete(self, request, object_id):
        with transaction.atomic(using=router.db_for_write(self.model_admin.model)):
            opts = self.model_admin.model._meta

            # Validate the reverse to field reference.
            to_field = request.query_params.get(TO_FIELD_VAR)
            if to_field and not self.model_admin.to_field_allowed(request, to_field):
                return Response({'detail': _('The field %s cannot be referenced.' % to_field)},
                                status=status.HTTP_400_BAD_REQUEST)

            obj = self.model_admin.get_object(
                request, unquote(object_id), to_field)

            # Check delete object permission
            if not self.model_admin.has_delete_permission(request):
                raise PermissionDenied

            if obj is None:
                msg = _("%(name)s with ID “%(key)s” doesn't exist. Perhaps it was deleted?") % {
                    "name": opts.verbose_name,
                    "key": unquote(object_id),
                }
                return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)

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

            return Response({"detail": _("Cannot delete %(name)s")
                             % {"name": str(opts.verbose_name)}},
                            status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_("Successfully deleted the selected objects"),
                response=dict,
                examples=[
                    OpenApiExample(
                        name=_("Delete Success Response"),
                        summary=_("Example of a successful delete operation"),
                        description=_(
                            "Returns a success message after deleting the selected objects"),
                        value={
                            "detail": "The object was deleted successfully."
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def post(self, *args, **kwargs):
        return self.delete(*args, **kwargs)
