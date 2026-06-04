import copy

from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from django_api_admin.utils.quote import unquote
from django_api_admin.admins.model_admin import TO_FIELD_VAR
from django_api_admin.openapi import (
    CommonAPIResponses,
    CommonAPIPathParams,
    CommonAPIQueryParams,
)


class DetailView(APIView):
    """
    Retrieves a single instance of the model identified by the provided `object_id`,
    supporting optional reverse lookups via the `to_field` query parameter, and
    performing permission checks.
    """

    serializer_class = None
    permission_classes = []
    model_admin = None

    @extend_schema(
        parameters=[
            CommonAPIPathParams.object_id,
            CommonAPIQueryParams.to_field,
        ],
        responses={
            200: OpenApiResponse(
                description=_("Serialized instance of the model"),
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        },
    )
    def get(self, request, object_id):
        # Validate the reverse to field reference
        to_field = request.query_params.get(TO_FIELD_VAR)
        if to_field and not self.model_admin.to_field_allowed(request, to_field):
            return Response({"detail": _("The field %s cannot be referenced.") % to_field}, status=status.HTTP_400_BAD_REQUEST)

        obj = self.model_admin.get_object(request, unquote(object_id), to_field)

        # If the object doesn't exist respond with not found
        if obj is None:
            msg = _("%(name)s with ID “%(key)s” doesn't exist. Perhaps it was deleted?") % {
                "name": self.model_admin.model._meta.verbose_name,
                "key": unquote(object_id),
            }
            return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(obj, context={"request": request})
        data = copy.deepcopy(serializer.data)

        return Response(data, status=status.HTTP_200_OK)
