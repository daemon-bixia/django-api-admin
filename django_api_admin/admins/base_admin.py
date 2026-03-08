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

import copy
from functools import partial

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_permission_codename
from django.utils.safestring import mark_safe

from rest_framework import serializers

from django_api_admin.checks import BaseAPIModelAdminChecks
from django_api_admin.utils.flatten_fieldsets import flatten_fieldsets
from django_api_admin.utils.modelserializer_factory import modelserializer_factory
from django_api_admin.exceptions import NotRegistered
from django_api_admin.fields import MethodField


def get_content_type_for_model(obj):
    # Since this module gets imported in the application's root package,
    # it cannot import models from other applications at the module level.
    from django.contrib.contenttypes.models import ContentType

    return ContentType.objects.get_for_model(obj, for_concrete_model=False)


class BaseAPIModelAdmin:
    """
    Shared behavior between APIModelAdmin, APIInlineModelAdmin.
    """
    autocomplete_fields = ()
    raw_id_fields = ()
    fields = None
    exclude = None
    fieldsets = None
    serializer_class = serializers.ModelSerializer
    filter_vertical = ()
    filter_horizontal = ()
    radio_fields = {}
    prepopulated_fields = {}
    serializerfield_overrides = {}
    readonly_fields = ()
    ordering = None
    sortable_by = None
    view_on_site = True
    show_full_result_count = True
    checks_class = BaseAPIModelAdminChecks

    # These are the options used to customize the change/add page UI
    # server-side customizations like `exclude`, and `ordering` are not included
    form_options = [
        'fieldsets', 'fields',
        'save_on_top', 'save_as', 'save_as_continue',
        'view_on_site', 'radio_fields', 'prepopulated_fields',
        'filter_horizontal', 'filter_vertical', 'raw_id_fields',
        'autocomplete_fields'
    ]

    def check(self, **kwargs):
        return self.checks_class().check(self, **kwargs)

    def serializerfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Hook for specifying the kwargs for the serializer Field's constructor
        for a given database Field instance.

        If kwargs are given, they're passed to the serializer Field's constructor.
        This method only runs if the field is not declared in the serializer_class.
        """
        # Call the hook for the choice field
        if db_field.choices:
            return self.serializerfield_for_choice_field(db_field, request, **kwargs)

        # Call the hooks for the relational fields
        if isinstance(db_field, (models.ForeignKey, models.ManyToManyField)):
            if db_field.__class__ in self.serializerfield_overrides:
                kwargs = {
                    **self.serializerfield_overrides[db_field.__class__], **kwargs}

            if isinstance(db_field, models.ForeignKey):
                kwargs = self.serializerfield_for_foreignkey(
                    db_field, request, **kwargs)
            elif isinstance(db_field, models.ManyToManyField):
                kwargs = self.serializerfield_for_manytomany(
                    db_field, request, **kwargs)

            return kwargs

        # If we've got overrides for the serializerfield defined, use 'em. **kwargs
        # passed to serializerfield_for_dbfield override the defaults.
        for klass in db_field.__class__.mro():
            if klass in self.serializerfield_overrides:
                return {
                    **copy.deepcopy(self.serializerfield_overrides[klass]), **kwargs}

        return kwargs

    def serializerfield_for_choice_field(self, db_field, request, **kwargs):
        """
        Get the kwargs for the serializer Field's constructor for a database
        Field that has declared choices.
        """
        return kwargs

    def get_field_queryset(self, db, db_field, request):
        """
        If the ModelAdmin specifies ordering, the queryset should respect that
        ordering. Otherwise don't specify the queryset, let the field decide
        (return None in that case).
        """
        try:
            related_admin = self.admin_site.get_model_admin(
                db_field.remote_field.model)
        except NotRegistered:
            return None
        else:
            ordering = related_admin.get_ordering(request)
            if ordering is not None and ordering != ():
                return db_field.remote_field.model._default_manager.order_by(
                    *ordering
                )
        return None

    def serializerfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Get the kwargs for the serializer Field's constructor for a ForeignKey.
        """
        db = kwargs.get("using")

        if "queryset" not in kwargs:
            queryset = self.get_field_queryset(db, db_field, request)
            if queryset is not None:
                kwargs["queryset"] = queryset

        return kwargs

    def serializerfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Get the kwargs for the serializer Field's constrcutor for a ManyToManyField.
        """
        if not db_field.remote_field.through._meta.auto_created:
            return None
        db = kwargs.get("using")

        if "queryset" not in kwargs:
            queryset = self.get_field_queryset(db, db_field, request)
            if queryset is not None:
                kwargs["queryset"] = queryset

        return kwargs

    def get_autocomplete_fields(self, request):
        """
        Return a list of ForeignKey and/or ManyToMany fields which should use
        an autocomplete widget.
        """
        return self.autocomplete_fields

    def get_view_on_site_url(self, obj=None):
        if obj is None or not self.view_on_site:
            return None

        if callable(self.view_on_site):
            return self.view_on_site(obj)
        elif hasattr(obj, "get_absolute_url"):
            # Use the ContentType lookup if view_on_site is True
            return reverse(
                f"{self.admin_site.name}:view_on_site",
                kwargs={
                    "content_type_id": get_content_type_for_model(obj).pk,
                    "object_id": obj.pk,
                },
                current_app=self.admin_site.name,
            )

    def get_serializer_class(self, request, obj=None, change=False, **kwargs):
        """
        Return a serializer class to be used in the model admin views
        """
        if "fields" in kwargs:
            fields = kwargs.pop("fields")
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))

        # Get excluded fields
        excluded = self.get_exclude(request, obj)
        exclude = [] if excluded is None else list(excluded)
        readonly = self.get_readonly_fields(request, obj)
        readonly_fields = [] if readonly is None else list(readonly)

        # Exclude all fields if it's a request and the user doesn't have
        # the change permission.
        if (
            change
            and hasattr(request, "user")
            and not self.has_change_permission(request, obj)
        ):
            exclude.extend(fields)

        # Take the serializer_class's Meta.exclude into account only if the
        # ModelAdmin doesn't define its own.
        if (
            excluded is None
            and hasattr(self.serializer_class, "Meta")
            and hasattr(self.serializer_class.Meta, "exclude")
        ):
            exclude.extend(self.serializer_class.Meta.exclude)

        callables = dict()
        # Include callables in `fields` as `MethodField`s
        if fields is not None:
            for field in fields:
                method = getattr(self, field, None) or getattr(
                    self.model, field, None)
                if field not in self.serializer_class._declared_fields and callable(method):
                    callables[field] = MethodField(method)

        # Remove serializer fields declared in excluded.
        new_attrs = {
            **dict.fromkeys(f for f in exclude if f in self.serializer_class._declared_fields),
            **callables
        }
        serializer_class = type(
            self.serializer_class.__name__,
            (self.serializer_class,),
            new_attrs
        )

        # Remove the excluded fields from the `fields` delcared in the model_admin.
        if fields is not None:
            fields = [f for f in fields if f not in exclude]
            exclude = None

            # Always add the primary key to `readonly_fields` and `fields` to identity the object
            if 'pk' not in fields:
                fields.append('pk')
            if 'pk' not in readonly_fields:
                readonly_fields.append('pk')

        defaults = {
            "serializer_class": serializer_class,
            "fields": fields,
            "exclude": exclude,
            "read_only_fields": readonly_fields,
            "serializerfield_callback": partial(self.serializerfield_for_dbfield, request=request),
            **kwargs,
        }

        return modelserializer_factory(self.model, **defaults)

    def get_empty_value_display(self):
        """
        Return the empty_value_display set on APIModelAdmin or APIAdminSite.
        """
        try:
            return mark_safe(self.empty_value_display)
        except AttributeError:
            return mark_safe(self.admin_site.empty_value_display)

    def get_exclude(self, request, obj=None):
        """
        Hook for specifying exclude.
        """
        return self.exclude

    def get_fields(self, request, obj):
        """
        Hook for specifying fields.
        """
        if self.fields:
            return self.fields
        serializer_class = self.get_serializer_class(request, obj, fields=None)
        return [*serializer_class().fields, *self.get_readonly_fields(request, obj)]

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """
        if self.fieldsets:
            return self.fieldsets
        return [(None, {"fields": self.get_fields(request, obj)})]

    def get_inlines(self, request, obj):
        """Hook for specifying custom inlines."""
        return self.inlines

    def get_ordering(self, request):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)

    def get_readonly_fields(self, request, obj=None):
        """
        Hook for specifying custom readonly fields.
        """
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        """
        Hook for specifying custom prepopulated fields.
        """
        return self.prepopulated_fields

    def get_queryset(self, request):
        """
        Return a QuerySet of all model instances that can be edited by the
        admin site. This is used by get_changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_sortable_by(self, request):
        """Hook for specifying which fields can be sorted in the changelist."""
        return (
            self.sortable_by
            if self.sortable_by is not None
            else self.get_list_display(request)
        )

    def get_list_view(self):
        from django_api_admin.admin_views.model_admin_views.list import ListView

        defaults = {
            'serializer_class': self.get_serializer_class(None),
            'permission_classes': self.admin_site.get_permission_classes(),
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self,
        }
        return ListView.as_view(**defaults)

    def get_detail_view(self):
        from django_api_admin.admin_views.model_admin_views.detail import DetailView

        defaults = {
            'serializer_class': self.get_serializer_class(None),
            'permission_classes': self.admin_site.get_permission_classes(),
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self
        }
        return DetailView.as_view(**defaults)

    def get_add_view(self):
        from django_api_admin.admin_views.model_admin_views.add import AddView

        defaults = {
            'serializer_class': self.get_serializer_class(None),
            'permission_classes': self.admin_site.get_permission_classes(),
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self,
        }
        return AddView.as_view(**defaults)

    def get_change_view(self):
        from django_api_admin.admin_views.model_admin_views.change import ChangeView

        defaults = {
            'serializer_class': self.get_serializer_class(None),
            'permission_classes': self.admin_site.get_permission_classes(),
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self,
        }
        return ChangeView.as_view(**defaults)

    def get_delete_view(self):
        from django_api_admin.admin_views.model_admin_views.delete import DeleteView

        defaults = {
            'permission_classes': self.admin_site.get_permission_classes(),
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self
        }
        return DeleteView.as_view(**defaults)

    def has_add_permission(self, request):
        """
        Return True if the given request has permission to add an object.
        Can be overridden by the user in subclasses.
        """
        opts = self.opts
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        """
        Return True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self.opts
        codename = get_permission_codename('change', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_delete_permission(self, request, obj=None):
        """
        Return True if the given request has permission to delete the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self.opts
        codename = get_permission_codename('delete', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_view_permission(self, request, obj=None):
        """
        Return True if the given request has permission to view the given
        Django model instance. The default implementation doesn't examine the
        `obj` parameter.

        If overridden by the user in subclasses, it should return True if the
        given request has permission to view the `obj` model instance. If `obj`
        is None, it should return True if the request has permission to view
        any object of the given type.
        """
        opts = self.opts
        codename_view = get_permission_codename('view', opts)
        codename_change = get_permission_codename('change', opts)
        return (
            request.user.has_perm('%s.%s' % (opts.app_label, codename_view)) or
            request.user.has_perm('%s.%s' % (opts.app_label, codename_change))
        )

    def has_view_or_change_permission(self, request, obj=None):
        return self.has_view_permission(request) or self.has_change_permission(request)

    def has_module_permission(self, request):
        """
        Return True if the given request has any permission in the given
        app label.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to view the module on
        the admin index page and access the module's index page. Overriding it
        does not restrict access to the add, change or delete views. Use
        `ModelAdmin.has_(add|change|delete)_permission` for that.
        """
        return request.user.has_module_perms(self.opts.app_label)

    @property
    def is_inline(self):
        from django_api_admin.admins.inline_admin import InlineAPIModelAdmin
        return isinstance(self, InlineAPIModelAdmin)
