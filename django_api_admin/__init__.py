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

from django_api_admin.utils.module_loading import autodiscover_modules
from django_api_admin.decorators import action, display, register
from django_api_admin.filters import (
    AllValuesFieldListFilter,
    BooleanFieldListFilter,
    ChoicesFieldListFilter,
    DateFieldListFilter,
    EmptyFieldListFilter,
    FieldListFilter,
    ListFilter,
    RelatedFieldListFilter,
    RelatedOnlyFieldListFilter,
    SimpleListFilter,
)
from django_api_admin.admins.model_admin import APIModelAdmin, HORIZONTAL, VERTICAL
from django_api_admin.admins.inline_admin import StackedInlineAPI, TabularInlineAPI
from django_api_admin.sites import APIAdminSite, site

__all__ = [
    "action",
    "display",
    "register",
    "APIModelAdmin",
    "HORIZONTAL",
    "VERTICAL",
    "StackedInlineAPI",
    "TabularInlineAPI",
    "APIAdminSite",
    "site",
    "ListFilter",
    "SimpleListFilter",
    "FieldListFilter",
    "BooleanFieldListFilter",
    "RelatedFieldListFilter",
    "ChoicesFieldListFilter",
    "DateFieldListFilter",
    "AllValuesFieldListFilter",
    "EmptyFieldListFilter",
    "RelatedOnlyFieldListFilter",
    "autodiscover",
]


def autodiscover():
    autodiscover_modules("admin", register_to=site)
