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

import json
from types import SimpleNamespace

from django.core.exceptions import SuspiciousOperation

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated


class NotRelationField(Exception):
    pass


class IncorrectLookupParameters(Exception):
    pass


class FieldIsAForeignKeyColumnName(Exception):
    """A field is a foreign key attname, i.e. <FK>_id."""

    pass


class DisallowedModelAdminLookup(SuspiciousOperation):
    """Invalid filter was passed to admin view via URL querystring"""

    pass


class DisallowedModelAdminToField(SuspiciousOperation):
    """Invalid to_field was passed to admin view via URL query string"""

    pass


class AlreadyRegistered(Exception):
    """The model is already registered."""

    pass


class NotRegistered(Exception):
    """The model is not registered."""

    pass


def allauth_exception_handler(exc, context):
    """
    Custom exception handler that translates DRF `NotAuthenticated`
    errors into the same JSON payload shape returned by `django-allauth`
    headless endpoints.
    """
    from allauth.headless.base.response import AuthenticationResponse
    from allauth.headless.constants import Client

    response = exception_handler(exc, context)

    if isinstance(exc, NotAuthenticated):
        request = context.get("request")
        if request is not None:
            raw_request = getattr(request, "_request", request)

            # Ensure the request has the ``allauth.headless`` attributes that
            # the ``AuthenticationResponse`` class expects.
            raw_request.allauth = SimpleNamespace()
            raw_request.allauth.headless = SimpleNamespace()
            client_type = Client.BROWSER
            if (hasattr(raw_request, "headers") and "X-Session-Token" in raw_request.headers) or raw_request.META.get(
                "HTTP_X_SESSION_TOKEN"
            ):
                client_type = Client.APP
            raw_request.allauth.headless.client = client_type

            allauth_response = AuthenticationResponse(raw_request)
            try:
                data = json.loads(allauth_response.content.decode("utf-8"))
            except Exception:
                data = {}

            drf_response = Response(data, status=status.HTTP_401_UNAUTHORIZED)
            # Preserve any cookies / headers set by the allauth response.
            drf_response.cookies = allauth_response.cookies
            for header, value in allauth_response.headers.items():
                drf_response[header] = value

            return drf_response

    return response


def admin_exception_handler(exc, context):
    """
    Custom exception handler that changes DRF errors
    errors into the format used by `django_api_admin`.
    """
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict) and "detail" in response.data and len(response.data) == 1:
            response.data = {"status": response.status_code}

    return response
