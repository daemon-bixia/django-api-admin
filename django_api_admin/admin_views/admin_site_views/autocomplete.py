# -----------------------------------------------------------------------------
# Portions of this file are from Django (https://www.djangoproject.com/)
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
# Licensed under the BSD 3-Clause License.
#
# Additional code copyright (c) 2021 Muhammad Salah
# Licensed under the MIT License
#
# This file includes both Django code and your my own contributions.
# -----------------------------------------------------------------------------

from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import FieldDoesNotExist

from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.serializers import AutoCompleteSerializer, AutoCompleteResponseSerializer
from django_api_admin.openapi import CommonAPIResponses, CommonAPIQueryParams
from django_api_admin.mixins import APIAdminErrorViewMixin
from django_api_admin.exceptions import MissingSearchFields


class AutoCompleteView(APIAdminErrorViewMixin, APIView):
    """
    Handles the "search-as-you-type" functionality.
    It extracts search parameters, validates user permissions,
    retrieves the relevant queryset, paginates the results,
    and returns them as a JSON response.
    """

    permission_classes = []
    admin_site = None

    paginate_orphans = 0
    page_kwarg = "page"
    allow_empty = True
    paginate_by = 20

    @extend_schema(
        operation_id="Retrieve autocomplete results",
        parameters=[AutoCompleteSerializer, CommonAPIQueryParams.page],
        responses={
            200: OpenApiResponse(
                description=_("List of objects matching the search term"),
                response=AutoCompleteResponseSerializer,
            ),
            400: CommonAPIResponses.bad_request(),
            401: CommonAPIResponses.unauthorized(),
            403: CommonAPIResponses.permission_denied(),
            404: CommonAPIResponses.not_found(_("Source model or field not found, or related model not registered in admin.")),
            409: CommonAPIResponses.conflict(_("source model_admin missing search_fields.")),
        },
    )
    def get(self, request):
        try:
            (
                self.term,
                self.model_admin,
                self.source_field,
                to_field_name,
            ) = self.process_request(request)
        except MissingSearchFields:
            return Response(
                {"status": status.HTTP_409_CONFLICT},
                status=status.HTTP_409_CONFLICT,
            )

        if not self.has_perm(request):
            raise PermissionDenied

        self.object_list = self.get_queryset(request)
        context = self.get_context_data()

        return Response(
            {
                "status": status.HTTP_200_OK,
                "data": {
                    "results": [self.serialize_result(obj, to_field_name) for obj in context["object_list"]],
                    "pagination": {"more": context["page_obj"].has_next()},
                },
            },
            status=status.HTTP_200_OK,
        )

    def serialize_result(self, obj, to_field_name):
        """
        Convert the provided model object to a dictionary that is added to the
        results list.
        """
        return {"id": str(getattr(obj, to_field_name)), "text": str(obj)}

    def get_queryset(self, request):
        """Return queryset based on model_admin.get_search_results()."""
        qs = self.model_admin.get_queryset(request)
        qs = qs.complex_filter(self.source_field.get_limit_choices_to())
        qs, search_use_distinct = self.model_admin.get_search_results(request, qs, self.term)
        if search_use_distinct:
            qs = qs.distinct()
        return qs

    def process_request(self, request):
        """
        Validate request integrity, extract and return request parameters.

        Since the subsequent view permission check requires the target model
        admin, which is determined here, raise PermissionDenied if the
        requested app, model or field are malformed.

        Raise Http404 if the target model admin is not configured properly with
        search_fields.
        """
        term = request.GET.get("term", "")

        try:
            app_label = request.GET["app_label"]
            model_name = request.GET["model_name"]
            field_name = request.GET["field_name"]
        except KeyError as e:
            raise ValidationError([{"message": _("missing values app_label, model_name, and field_name"), "params": e}])

        # Retrieve objects from parameters.
        try:
            source_model = apps.get_model(app_label, model_name)
        except LookupError:
            raise NotFound()
        try:
            source_field = source_model._meta.get_field(field_name)
        except FieldDoesNotExist:
            raise NotFound()
        try:
            remote_model = source_field.remote_field.model
        except AttributeError:
            raise NotFound()
        try:
            model_admin = self.admin_site.get_model_admin(remote_model)
        except KeyError:
            raise NotFound()

        # Validate suitability of objects.
        if not getattr(model_admin, "search_fields"):
            raise MissingSearchFields

        to_field_name = getattr(source_field.remote_field, "field_name", remote_model._meta.pk.attname)
        to_field_name = remote_model._meta.get_field(to_field_name).attname
        if not model_admin.to_field_allowed(request, to_field_name):
            raise PermissionDenied

        return term, model_admin, source_field, to_field_name

    def has_perm(self, request):
        """Check if user has permission to access the related model."""
        return self.model_admin.has_view_permission(request)

    def get_context_data(self, object_list=None, **kwargs):
        """Get the context for this view."""
        queryset = object_list if object_list is not None else self.object_list
        context_object_name = "%s_list" % queryset.model._meta.model_name
        if self.paginate_by:
            paginator = self.model_admin.get_paginator(
                self.request,
                queryset,
                self.paginate_by,
                self.paginate_orphans,
                self.allow_empty,
            )
            page, queryset, is_paginated = self.model_admin.admin_site.paginate_queryset(
                self.request, paginator, self.page_kwarg
            )
            context = {
                "paginator": paginator,
                "page_obj": page,
                "is_paginated": is_paginated,
                "object_list": queryset,
            }
        else:
            context = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": queryset,
            }
        if context_object_name is not None:
            context[context_object_name] = queryset
        context.update(kwargs)
        context.setdefault("view", self)
        return context
