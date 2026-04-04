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

import enum
import traceback
from functools import update_wrapper, partial

from django.db import models
from django.urls import path, include
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.utils.text import capfirst, smart_split, unescape_string_literal

from rest_framework import status
from rest_framework import serializers
from rest_framework.utils import model_meta
from rest_framework.response import Response

from django_api_admin.constants.vars import LOOKUP_SEP
from django_api_admin.checks import APIModelAdminChecks
from django_api_admin.admins.base_admin import BaseAPIModelAdmin
from django_api_admin.utils.model_format_dict import model_format_dict
from django_api_admin.utils.modelserializer_factory import modelserializer_factory
from django_api_admin.utils.lookup_spawns_duplicates import lookup_spawns_duplicates
from django_api_admin.utils.construct_change_message import construct_change_message


class ShowFacets(enum.Enum):
    NEVER = "NEVER"
    ALLOW = "ALLOW"
    ALWAYS = "ALWAYS"


class APIModelAdmin(BaseAPIModelAdmin):
    """Encapsulate all admin options and functionality for a given model."""

    list_display = ("__str__",)
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    search_help_text = None
    date_hierarchy = None
    save_as = False
    save_as_continue = True
    save_on_top = False
    paginator = Paginator
    show_facets = ShowFacets.ALLOW
    inlines = ()

    # Actions
    actions = ()
    action_serializer = None
    actions_on_top = True
    actions_on_bottom = False
    actions_selection_counter = True
    checks_class = APIModelAdminChecks

    # These are the admin options used to customize the change list page UI
    # server-side customizations like `list_select_related` and `actions` are not included
    changelist_options = [
        'actions_on_top', 'actions_on_bottom', 'actions_selection_counter',
        'empty_value_display', 'list_display', 'list_display_links', 'list_editable', 'exclude',
        'show_full_result_count', 'list_per_page', 'list_max_show_all',
        'date_hierarchy', 'search_help_text', 'sortable_by', 'search_fields', 'preserve_filters',
    ]

    def __init__(self, model, admin_site):
        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site

    def __str__(self):
        return "%s.%s" % (self.opts.app_label, self.__class__.__name__)

    def __repr__(self):
        return (
            f"<{self.__class__.__qualname__}: model={self.model.__qualname__} "
            f"site={self.admin_site!r}>"
        )

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        for inline_class in self.inlines:
            inline = inline_class(self.model, self.admin_site)
            if request:
                if not (
                    inline.has_view_or_change_permission(request)
                    or inline.has_add_permission(request)
                    or inline.has_delete_permission(request)
                ):
                    continue
                if not inline.has_add_permission(request):
                    inline.max_num = 0
            inline_instances.append(inline)

        return inline_instances

    def get_urls(self):

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = f'{self.model._meta.app_label}_{self.model._meta.model_name}'
        prefix = f'{self.model._meta.app_label}/{self.model._meta.model_name}'
        urlpatterns = [
            path(f'{prefix}/list/', wrap(self.get_list_view()),
                 name=f'{info}_list'),
            path(f'{prefix}/changelist/',
                 wrap(self.get_changelist_view()), name=f'{info}_changelist'),
            path(f'{prefix}/perform_action/',
                 wrap(self.get_handle_action_view()), name=f'{info}_perform_action'),
            path(f'{prefix}/add/', wrap(self.get_add_view()), name=f'{info}_add'),
            path(f'{prefix}/<path:object_id>/detail/',
                 wrap(self.get_detail_view()), name=f'{info}_detail'),
            path(f'{prefix}/<path:object_id>/delete/',
                 wrap(self.get_delete_view()), name=f'{info}_delete'),
            path(f'{prefix}/<path:object_id>/history/',
                 wrap(self.get_history_view()), name=f'{info}_history'),
            path(f'{prefix}/<path:object_id>/change/',
                 wrap(self.get_change_view()), name=f'{info}_change'),
        ]

        # Add Inline admins urls
        for inline_admin in self.get_inline_instances(None):
            urlpatterns.append(
                path(f'{prefix}/inlines/', include(inline_admin.urls)))

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls()

    def get_model_perms(self, request):
        """
        Return a dict of all perms for this model. This dict has the keys
        ``add``, ``change``, ``delete``, and ``view`` mapping to the True/False
        for each of those actions.
        """
        return {
            "add": self.has_add_permission(request),
            "change": self.has_change_permission(request),
            "delete": self.has_delete_permission(request),
            "view": self.has_view_permission(request),
        }

    def get_changelist(self, request, **kwargs):
        """
        Return the ChangeList class for use on the changelist page.
        """
        from django_api_admin.changelist import ChangeList

        return ChangeList

    def get_changelist_instance(self, request):
        """
        Return a `ChangeList` instance based on `request`. May raise
        `IncorrectLookupParameters`.
        """
        list_display = self.list_display
        list_display_links = self.get_list_display_links(request, list_display)
        # Add the action checkboxes if any actions are available.
        if self.get_actions(request):
            list_display = ["action_checkbox", *list_display]
        sortable_by = self.get_sortable_by(request)
        ChangeList = self.get_changelist(request)
        return ChangeList(
            request,
            self.model,
            list_display,
            list_display_links,
            self.get_list_filter(request),
            self.date_hierarchy,
            self.get_search_fields(request),
            self.get_list_select_related(request),
            self.list_per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
            sortable_by,
            self.search_help_text
        )

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

    def get_changelist_serializer_class(self, request, **kwargs):
        """
        Return a Serializer class for use on the changelist page if list_editable
        is used.
        """
        defaults = {
            "serializerfield_callback": partial(self.serializerfield_for_dbfield, request=request),
            **kwargs,
        }
        return modelserializer_factory(
            self.model,
            self.serializer_class,
            fields=self.list_editable,
            **defaults,
        )

    def get_serializer_classes_with_inlines(self, request, obj=None):
        """
        Yield formsets and the corresponding inlines.
        """
        for inline in self.get_inline_instances(request, obj):
            yield inline.get_serializer_class(request, obj), inline

    def get_paginator(
        self, request, queryset, per_page, orphans=0, allow_empty_first_page=True
    ):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def log_addition(self, request, obj, message):
        """
        Log that an object has been successfully added.
        The default implementation creates an admin LogEntry object.
        """
        from django_api_admin.models import ADDITION, LogEntry

        return LogEntry.objects.log_actions(
            user_id=request.user.pk,
            queryset=[obj],
            action_flag=ADDITION,
            change_message=message,
            single_object=True
        )

    def log_change(self, request, obj, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        from django_api_admin.models import CHANGE, LogEntry

        return LogEntry.objects.log_actions(
            user_id=request.user.pk,
            queryset=[obj],
            action_flag=CHANGE,
            change_message=message,
            single_object=True,
        )

    def log_deletion(self, request, queryset):
        """
        Log that an object will be deleted. Note that this method must be
        called before the deletion.

        The default implementation creates an admin LogEntry object.
        """
        from django_api_admin.models import DELETION, LogEntry

        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            queryset=queryset,
            action_flag=DELETION,
        )

    @staticmethod
    def _get_action_description(func, name):
        try:
            return func.short_description
        except AttributeError:
            return capfirst(name.replace("_", " "))

    def _get_base_actions(self):
        """Return the list of actions, prior to any request-based filtering."""
        actions = []
        base_actions = (self.get_action(action)
                        for action in self.actions or [])
        # get_action might have returned None, so filter any of those out.
        base_actions = [action for action in base_actions if action]
        base_action_names = {name for _, name, _ in base_actions}

        # Gather actions from the admin site first
        for name, func in self.admin_site.actions:
            if name in base_action_names:
                continue
            description = self._get_action_description(func, name)
            actions.append((func, name, description))
        # Add actions from this ModelAdmin.
        actions.extend(base_actions)
        return actions

    def _filter_actions_by_permissions(self, request, actions):
        """Filter out any actions that the user doesn't have access to."""
        filtered_actions = []
        for action in actions:
            callable = action[0]
            if not hasattr(callable, "allowed_permissions"):
                filtered_actions.append(action)
                continue
            permission_checks = (
                getattr(self, "has_%s_permission" % permission)
                for permission in callable.allowed_permissions
            )
            if any(has_permission(request) for has_permission in permission_checks):
                filtered_actions.append(action)
        return filtered_actions

    def get_actions(self, request):
        """
        Return a dictionary mapping the names of all actions for this
        ModelAdmin to a tuple of (callable, name, description) for each action.
        """
        # If self.actions is set to None that means actions are disabled on
        # this page.
        if self.actions is None:
            return {}
        actions = self._filter_actions_by_permissions(
            request, self._get_base_actions())
        return {name: (func, name, desc) for func, name, desc in actions}

    def get_action_choices(self, request, default_choices=models.BLANK_CHOICE_DASH):
        """
        Return a list of choices for use in a form object.  Each choice is a
        tuple (name, description).
        """
        choices = [*default_choices]
        for func, name, description in self.get_actions(request).values():
            choice = (name, description % model_format_dict(self.opts, models))
            choices.append(choice)
        return choices

    def get_action(self, action):
        """
        Return a given action from a parameter, which can either be a callable,
        or the name of a method on the ModelAdmin.  Return is a tuple of
        (callable, name, description).
        """
        # If the action is a callable, just use it.
        if callable(action):
            func = action
            action = action.__name__

        # Next, look for a method. Grab it off self.__class__ to get an unbound
        # method instead of a bound one; this ensures that the calling
        # conventions are the same for functions and methods.
        elif hasattr(self.__class__, action):
            func = getattr(self.__class__, action)

        # Finally, look for a named method on the admin site
        else:
            try:
                func = self.admin_site.get_action(action)
            except KeyError:
                return None

        description = self._get_action_description(func, action)
        return func, action, description

    def get_action_serializer(self, request):
        from django_api_admin.serializers import ActionSerializer

        action_serializer = self.action_serializer or ActionSerializer

        # Set the instances returned by `self.get_queryset` by of this model as choices
        choices = []
        queryset = self.get_queryset(request)
        for item in queryset:
            choices.append((f'{item.pk}', f'{str(item)}'))

        # Dynamicall create an instace of the self.action_serializer with the `action` choices
        # being the actions defined in the model_admin and the `selected_ids` being the `choices`
        return type(f'{self.model.__name__}ActionSerializer', (action_serializer,), {
            'action': serializers.ChoiceField(choices=[*self.get_action_choices(request)]),
            'selected_ids': serializers.MultipleChoiceField(choices=[*choices])
        })

    def get_list_display(self, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        return self.list_display

    def get_list_display_links(self, request, list_display):
        """
        Return a sequence containing the fields to be displayed as links
        on the changelist. The list_display parameter is the list of fields
        returned by get_list_display().
        """
        if (
            self.list_display_links
            or self.list_display_links is None
            or not list_display
        ):
            return self.list_display_links
        else:
            # Use only the first item in list_display as link
            return list(list_display)[:1]

    def get_list_filter(self, request):
        """
        Return a sequence containing the fields to be displayed as filters in
        the right sidebar of the changelist page.
        """
        return self.list_filter

    def get_list_select_related(self, request):
        """
        Return a list of fields to add to the select_related() part of the
        changelist items query.
        """
        return self.list_select_related

    def get_search_fields(self, request):
        """
        Return a sequence containing the fields to be searched whenever
        somebody submits a search query.
        """
        return self.search_fields

    def get_search_results(self, request, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """

        # Apply keyword searches.
        def construct_search(field_name):
            """
            Return a tuple of (lookup, field_to_validate).

            field_to_validate is set for non-text exact lookups so that
            invalid search terms can be skipped (preserving index usage).
            """
            if field_name.startswith("^"):
                return "%s__istartswith" % field_name.removeprefix("^"), None
            elif field_name.startswith("="):
                return "%s__iexact" % field_name.removeprefix("="), None
            elif field_name.startswith("@"):
                return "%s__search" % field_name.removeprefix("@"), None
            # Use field_name if it includes a lookup.
            opts = queryset.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            # Go through the fields, following all relations.
            prev_field = None
            for path_part in lookup_fields:
                if path_part == "pk":
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                except FieldDoesNotExist:
                    # Use valid query lookups.
                    if prev_field and prev_field.get_lookup(path_part):
                        if path_part == "exact" and not isinstance(
                            prev_field, (models.CharField, models.TextField)
                        ):
                            # Use prev_field to validate the search term.
                            return field_name, prev_field
                        return field_name, None
                else:
                    prev_field = field
                    if hasattr(field, "path_infos"):
                        # Update opts to follow the relation.
                        opts = field.path_infos[-1].to_opts
            # Otherwise, use the field with icontains.
            return "%s__icontains" % field_name, None

        may_have_duplicates = False
        search_fields = self.get_search_fields(request)
        if search_fields and search_term:
            orm_lookups = []
            for field in search_fields:
                orm_lookups.append(construct_search(str(field)))

            term_queries = []
            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                # Build term lookups, skipping values invalid for their field.
                bit_lookups = []
                for orm_lookup, validate_field in orm_lookups:
                    if validate_field is not None:
                        formfield = validate_field.formfield()
                        try:
                            if formfield is not None:
                                value = formfield.to_python(bit)
                            else:
                                # Fields like AutoField lack a form field.
                                value = validate_field.to_python(bit)
                        except ValidationError:
                            # Skip this lookup for invalid values.
                            continue
                    else:
                        value = bit
                    bit_lookups.append((orm_lookup, value))
                if bit_lookups:
                    or_queries = models.Q.create(
                        bit_lookups, connector=models.Q.OR)
                    term_queries.append(or_queries)
                else:
                    # No valid lookups: add a filter that returns nothing.
                    term_queries.append(models.Q(pk__in=[]))
            if term_queries:
                queryset = queryset.filter(models.Q.create(term_queries))
            may_have_duplicates |= any(
                lookup_spawns_duplicates(self.opts, search_spec)
                for search_spec, _ in orm_lookups
            )
        return queryset, may_have_duplicates

    def construct_change_message(self, request, serializer, serializers, add=False):
        """
        Construct a JSON structure describing changes from a changed object.
        """
        return construct_change_message(request, serializer, serializers, add)

    def get_changelist_view(self):
        from django_api_admin.admin_views.model_admin_views.changelist import ChangeListView

        defaults = {
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self
        }
        return ChangeListView.as_view(**defaults)

    def get_handle_action_view(self):
        from django_api_admin.admin_views.model_admin_views.handle_action import HandleActionView

        defaults = {
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self
        }
        return HandleActionView.as_view(**defaults)

    def get_history_view(self):
        from django_api_admin.admin_views.model_admin_views.history import HistoryView

        defaults = {
            'serializer_class': self.admin_site.log_entry_serializer,
            'authentication_classes': self.admin_site.get_authentication_classes(),
            'model_admin': self
        }
        return HistoryView.as_view(**defaults)

    def save_serializer(self, request, serializer, change):
        """
        Given a ModelSerializer return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        validated_data = {**serializer.validated_data}

        if change:
            serializers.raise_errors_on_nested_writes(
                'update', serializer, validated_data)
            info = model_meta.get_field_info(serializer.instance)

            # Simply set each attribute on the instance, and then save it.
            # Note that unlike `.create()` we don't need to treat many-to-many
            # relationships as being a special case. During updates we already
            # have an instance pk for the relationships to be associated with.
            m2m_fields = []
            for attr, value in validated_data.items():
                if attr in info.relations and info.relations[attr].to_many:
                    m2m_fields.append((attr, value))
                else:
                    setattr(serializer.instance, attr, value)

            # Save many-to-many relationships after the instance is updated.
            def save_m2m():
                # Note that many-to-many fields are set after updating instance.
                # Setting m2m fields triggers signals which could potentially change
                # updated instance and we do not want it to collide with .update()
                for attr, value in m2m_fields:
                    field = getattr(serializer.instance, attr)
                    field.set(value)

            # Add a method to the serializer to allow deferred
            # saving of m2m data.
            serializer.save_m2m = save_m2m

            return serializer.instance
        else:
            serializers.raise_errors_on_nested_writes(
                'create', serializer, validated_data)
            ModelClass = self.model

            # Remove many-to-many relationships from validated_data.
            # They are not valid arguments to the default `.create()` method,
            # as they require that the instance has already been saved.
            info = model_meta.get_field_info(ModelClass)
            many_to_many = {}
            for field_name, relation_info in info.relations.items():
                if relation_info.to_many and (field_name in validated_data):
                    many_to_many[field_name] = validated_data.pop(
                        field_name)

            try:
                instance = ModelClass(**validated_data)
            except TypeError:
                tb = traceback.format_exc()
                msg = (
                    'Got a `TypeError` when calling `%s.%s.create()`. '
                    'This may be because you have a writable field on the '
                    'serializer class that is not a valid argument to '
                    '`%s.%s.create()`. You may need to make the field '
                    'read-only, or override the %s.create() method to handle '
                    'this correctly.\nOriginal exception was:\n %s' %
                    (
                        ModelClass.__name__,
                        ModelClass._default_manager.name,
                        ModelClass.__name__,
                        ModelClass._default_manager.name,
                        serializer.__class__.__name__,
                        tb
                    )
                )
                raise TypeError(msg)

            # Save many-to-many relationships after the instance is created.
            def save_m2m():
                if many_to_many:
                    for field_name, value in many_to_many.items():
                        field = getattr(instance, field_name)
                        field.set(value)

            # Add a method to the serializer to allow deferred
            # saving of m2m data.
            serializer.save_m2m = save_m2m

            return instance

    def save_model(self, request, obj, serializer, change):
        """
        Given a model instance save it to the database.
        """
        obj.save()
        serializer.instance = obj

    def delete_model(self, request, obj):
        """
        Given a model instance delete it from the database.
        """
        obj.delete()

    def delete_queryset(self, request, queryset):
        """Given a queryset, delete it from the database."""
        queryset.delete()

    def save_inline_operation(self, request, serializer, inline_operation, change):
        """
        Given an inline serializer save it to the database.
        """
        for operation, inline_serializers in inline_operation.items():
            for inline_serializer in inline_serializers:
                if operation == "add":
                    inline_serializer.save()
                elif operation == "change":
                    inline_serializer[0].save()
                elif operation == "delete":
                    inline_serializer.instance.delete()

    def save_related(self, request, obj, serializer, bulk_operation, change):
        """
        Given the ``HttpRequest``, the parent ``ModelSerializer`` instance, the
        list of inline serializers and a boolean value based on whether the
        parent is being added or changed, save the related objects to the
        database. Note that at this point save_serializer() and save_model() have
        already been called.
        """
        serializer.save_m2m()
        for inline_operation in bulk_operation.result.values():
            self.save_inline_operation(
                request, serializer, inline_operation, change)

    def response_add(self, request, obj, serializer, bulk_operation):
        return Response({
            "detail": _(f'The {self.model._meta.verbose_name} “{str(obj)}” was added successfully.'),
            "data": serializer.data,
            "inlines": bulk_operation.validated_data,
        }, status=status.HTTP_201_CREATED)
