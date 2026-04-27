import json

from django.utils.translation import gettext_lazy as _
from django.apps import apps

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.models import LogEntry
from django_api_admin.openapi import CommonAPIResponses
from django_api_admin.serializers import LogEntrySerializer, HistoryViewRequestSerializer
from django_api_admin.utils.get_content_type_for_model import get_content_type_for_model


class HistoryView(APIView):
    "The 'history' admin view for the entire site."
    serializer_class = None
    permission_classes = []
    ordering_fields = ["action_time", "-action_time"]
    admin_site = None

    paginate_orphans = 0
    page_kwarg = "page"
    allow_empty = True
    paginate_by = 20

    @extend_schema(
        methods=["GET"],
        parameters=[HistoryViewRequestSerializer],
        responses={
            200: OpenApiResponse(
                response=LogEntrySerializer(many=True),
                description=_("Successfully retrieved admin log entries")
            ),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
        },
        description=_("Retrieve a list of admin log entries"),
        tags=["admin-log"]
    )
    def get(self, request):
        # Get the queryset
        ordering = self.request.query_params.get("o", "action_time")
        if ordering not in self.ordering_fields:
            raise KeyError
        action_list = LogEntry.objects.all().order_by(ordering)

        # Filter the queryset.
        app_label = self.request.query_params.get("app_label", None)
        model_name = self.request.query_params.get("model", None)
        if app_label is not None and model_name is not None:
            model = apps.get_model(app_label, model_name)
            action_list = action_list.filter(
                content_type=get_content_type_for_model(model),
            )

            object_id = self.request.query_params.get("object_id", None)
            if object_id is not None:
                action_list = action_list.filter(
                    object_id=object_id,
                )

        # Select the related instances
        action_list = action_list.select_related()

        # Check for change or view permissions
        for obj in action_list:
            model_admin = self.admin_site.get_model_admin(
                obj.content_type.model_class())
            if not model_admin.has_view_or_change_permission(request, obj):
                raise PermissionDenied

        # Paginate queryset
        paginator = self.admin_site.paginator(
            action_list,
            self.paginate_by,
            self.paginate_orphans,
            self.allow_empty,
        )
        page, queryset, is_paginated = self.admin_site.paginate_queryset(
            request, paginator, self.page_kwarg)
        serializer = self.serializer_class(queryset, many=True)

        return Response({
            "num_pages": paginator.num_pages,
            "count": paginator.count,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
            "object_list": self.serialize_messages(serializer.data),
        }, status=status.HTTP_200_OK)

    def serialize_messages(self, data):
        for idx, item in enumerate(data, start=0):
            data[idx]["change_message"] = json.loads(
                item["change_message"] or "[]")
        return data

    def get_config(self, page, queryset):
        return {
            "result_count": len(page),
            "full_result_count": queryset.count(),
        }
