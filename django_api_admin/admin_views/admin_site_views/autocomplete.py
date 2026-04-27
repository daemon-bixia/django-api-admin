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

from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from django_api_admin.serializers import AutoCompleteSerializer
from django_api_admin.openapi import CommonAPIResponses


class AutoCompleteView(APIView):
    """
    API view for handling autocomplete functionality in admin fields.
    """
    permission_classes = []
    admin_site = None

    paginate_orphans = 0
    page_kwarg = "page"
    allow_empty = True
    paginate_by = 20

    @extend_schema(
        parameters=[AutoCompleteSerializer],
        responses={
            200: OpenApiResponse(
                description=_("Successful autocomplete response"),
                response=AutoCompleteSerializer,
                examples=[
                    OpenApiExample(
                        name=_("Success Response"),
                        summary=_(
                            "Example of a successful autocomplete response"),
                        description="Returns matching records based on the search term",
                        value=[{
                            "id": 1,
                            "name": "Muhammad",
                            "age": 60,
                            "is_vip": True,
                            "date_joined": "2025-02-02T23:09:31.994853Z",
                            "title": None,
                            "user": 1,
                            "publisher": [1],
                            "pk": 1
                        }],
                        status_codes=["200"],
                    )
                ]
            ),
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized(),
        },
        description=_(
            "Endpoint for autocomplete functionality on model fields")
    )
    def get(self, request):
        """
        Process the request to extract search parameters,
        validates user permissions, retrieves the relevant queryset,
        paginates the results, and returns them as a JSON response.
        """
        (
            self.term,
            self.model_admin,
            self.source_field,
            to_field_name,
        ) = self.process_request(request)

        if not self.has_perm(request):
            raise PermissionDenied

        self.object_list = self.get_queryset(request)
        context = self.get_context_data()

        return Response(
            {
                "results": [
                    self.serialize_result(obj, to_field_name)
                    for obj in context["object_list"]
                ],
                "pagination": {"more": context["page_obj"].has_next}
            },
            status=status.HTTP_200_OK
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
        qs, search_use_distinct = self.model_admin.get_search_results(
            qs, self.term)
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
        except KeyError:
            raise ParseError(
                {"detail": _("missing values app_label, model_name, and field_name")})

        # Retrieve objects from parameters.
        try:
            source_model = apps.get_model(app_label, model_name)
        except LookupError:
            raise ParseError({"detail": _("source model not found")})
        try:
            source_field = source_model._meta.get_field(field_name)
        except FieldDoesNotExist:
            raise ParseError(
                {"detail": _(f"source field not found in source model {source_model._meta.verbose_name}")})
        try:
            remote_model = source_field.remote_field.model
        except AttributeError:
            raise ParseError(
                {"detail": _(f"unable to locate the related model using source field {source_field.name}")})
        try:
            model_admin = self.admin_site.get_model_admin(remote_model)
        except KeyError:
            raise ParseError(
                {"detail": _("the remote model is not registered in the admin")})

        # Validate suitability of objects.
        if not getattr(model_admin, "search_fields"):
            raise ParseError(_("%s must have search_fields for the autocomplete_view.") % type(
                model_admin).__qualname__)

        to_field_name = getattr(
            source_field.remote_field, "field_name", remote_model._meta.pk.attname
        )
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
        context_object_name = "%s_list" % object_list.model._meta.model_name
        if self.paginate_by:
            paginator = self.model_admin.get_paginator(
                self.request,
                queryset,
                self.paginate_by,
                self.paginate_orphans,
                self.allow_empty,
            )
            page, queryset, is_paginated = self.model_admin.admin_site.paginate_queryset(
                self.request, paginator, self.page_kwarg)
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
        if self.extra_context is not None:
            kwargs.update(self.extra_context)
        return context
