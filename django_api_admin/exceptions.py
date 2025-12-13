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

from django.core.exceptions import SuspiciousOperation


class NotRelationField(Exception):
    pass


class IncorrectLookupParameters(Exception):
    pass


class NotRelationField(Exception):
    pass


class FieldIsAForeignKeyColumnName(Exception):
    """A field is a foreign key attname, i.e. <FK>_id."""

    pass


class DisallowedModelAdminLookup(SuspiciousOperation):
    """Invalid filter was passed to admin view via URL querystring"""

    pass


class AlreadyRegistered(Exception):
    """The model is already registered."""

    pass


class NotRegistered(Exception):
    """The model is not registered."""

    pass
