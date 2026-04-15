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

from django.contrib.auth import get_permission_codename
from django.core.exceptions import ValidationError
from django.utils.text import format_lazy

from django_api_admin.admins.base_admin import BaseAPIModelAdmin
from django_api_admin.checks import InlineAPIModelAdminChecks


class InlineAPIModelAdmin(BaseAPIModelAdmin):
    """
    Edit models connected with a relationship in one page
    """
    model = None
    fk_name = None
    extra = 3
    min_num = None
    max_num = None
    verbose_name = None
    verbose_name_plural = None
    can_delete = True
    show_change_link = False
    admin_style = None
    checks_class = InlineAPIModelAdminChecks

    def __init__(self, parent_model, admin_site,):
        self.admin_site = admin_site
        self.parent_model = parent_model
        self.opts = self.model._meta
        self.has_registered_model = admin_site.is_registered(self.model)
        super().__init__()
        if self.verbose_name_plural is None:
            if self.verbose_name is None:
                self.verbose_name_plural = self.opts.verbose_name_plural
            else:
                self.verbose_name_plural = format_lazy(
                    "{}s", self.verbose_name)
        if self.verbose_name is None:
            self.verbose_name = self.opts.verbose_name

    def get_object(self, request, object_id, from_field=None):
        """
        Return an instance matching the field and value provided, the primary
        key is used if no field is provided. Return ``None`` if no match is
        found or the object_id fails validation.
        """
        queryset = self.get_queryset(request)
        model = queryset.model
        field = (
            model._meta.pk if from_field is None else model._meta.get_field(
                from_field)
        )
        try:
            object_id = field.to_python(object_id)
            return queryset.get(**{field.name: object_id})
        except (model.DoesNotExist, ValidationError, ValueError):
            return None

    def get_urls(self):
        from django.urls import path
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = f'{self.parent_model._meta.app_label}_{self.parent_model._meta.model_name}_{self.opts.app_label}_{self.opts.model_name}'
        prefix = f'{self.model._meta.model_name}'

        return [
            path(f'{prefix}/list/', wrap(self.get_list_view()),
                 name=f'{info}_list'),
            path(f'{prefix}/add/', wrap(self.get_add_view()), name=f'{info}_add'),
            path(f'{prefix}/<path:object_id>/detail/',
                 wrap(self.get_detail_view()), name=f'{info}_detail'),
            path(f'{prefix}/<path:object_id>/change/',
                 wrap(self.get_change_view()), name=f'{info}_change'),
            path(f'{prefix}/<path:object_id>/delete/',
                 wrap(self.get_delete_view()), name=f'{info}_delete'),
        ]

    @property
    def urls(self):
        return self.get_urls()

    def _has_any_perms_for_target_model(self, request, perms):
        """
        This method is called only when the ModelAdmin's model is for an
        ManyToManyField's implicit through model (if self.opts.auto_created).
        Return True if the user has any of the given permissions ('add',
        'change', etc.) for the model that points to the through model.
        """
        opts = self.opts
        # Find the target model of an auto-created many-to-many relationship.
        for field in opts.fields:
            if field.remote_field and field.remote_field.model != self.parent_model:
                opts = field.remote_field.model._meta
                break
        return any(
            request.user.has_perm(
                "%s.%s" % (opts.app_label, get_permission_codename(perm, opts))
            )
            for perm in perms
        )

    def has_add_permission(self, request, obj):
        if self.opts.auto_created:
            # Auto-created intermediate models don't have their own
            # permissions. The user needs to have the change permission for the
            # related model in order to be able to do anything with the
            # intermediate model.
            return self._has_any_perms_for_target_model(request, ["change"])
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self.opts.auto_created:
            # Same comment as has_add_permission().
            return self._has_any_perms_for_target_model(request, ["change"])
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if self.opts.auto_created:
            # Same comment as has_add_permission().
            return self._has_any_perms_for_target_model(request, ["change"])
        return super().has_delete_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        if self.opts.auto_created:
            # Same comment as has_add_permission(). The 'change' permission
            # also implies the 'view' permission.
            return self._has_any_perms_for_target_model(request, ["view", "change"])
        return super().has_view_permission(request)


class TabularInlineAPI(InlineAPIModelAdmin):
    admin_style = 'tabular'


class StackedInlineAPI(InlineAPIModelAdmin):
    admin_style = 'stacked'
