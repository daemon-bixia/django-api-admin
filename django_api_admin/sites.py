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

from copy import copy
from weakref import WeakSet
from functools import update_wrapper

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.urls import NoReverseMatch, path, re_path, include, reverse
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from django_api_admin import actions
from django_api_admin.admins.model_admin import APIModelAdmin
from django_api_admin.pagination import AdminLogPagination, AdminResultsListPagination
from django_api_admin.exceptions import AlreadyRegistered, NotRegistered

from rest_framework.exceptions import PermissionDenied

all_sites = WeakSet()


class APIAdminSite():
    """
    Encapsulates an instance of the django admin application.
    """
    # Default model admin class
    admin_class = APIModelAdmin

    # Optional views
    include_swagger_ui_view = True

    # Default serializers
    password_change_serializer = None
    log_entry_serializer = None
    user_serializer = None

    # Default result pagination style
    default_pagination_class = AdminResultsListPagination
    default_log_pagination_class = AdminLogPagination

    # Text to put at the end of each page's <title>.
    site_title = gettext_lazy("Django site admin")

    # Text to put in each page's <h1>.
    site_header = gettext_lazy("Django administration")

    # Text to put at the top of the admin index page.
    index_title = gettext_lazy("Site administration")

    # URL for the "View site" link at the top of each admin page.
    site_url = "/"

    # List of authentication classes used by the admin views that require authentication
    authentication_classes = None

    enable_nav_sidebar = True

    empty_value_display = "-"

    # Separate model_admin urls from site urls
    site_urls = []
    admin_urls = {}

    # Used for dynamically tagging views when generating schemas
    url_prefix = None

    def __init__(self, include_auth=True, name="api_admin"):
        from django.contrib.auth.models import Group
        from django_api_admin import serializers as api_serializers

        self.url_prefix = self.url_prefix or f'/{name}'

        # Set default serializers
        self.password_change_serializer = api_serializers.PasswordChangeSerializer
        self.log_entry_serializer = api_serializers.LogEntrySerializer
        self.user_serializer = api_serializers.UserSerializer

        self._registry = {}  # model_class class -> admin_class instance
        self.name = name
        all_sites.add(self)

        # Replace default delete selected with a custom delete_selected action
        self._actions = {'delete_selected': actions.delete_selected}
        self._global_actions = self._actions.copy()
        self.admin_class = self.admin_class or APIModelAdmin

        # If include_auth is set to True then include default UserModel and Groups
        UserModel = get_user_model()
        if include_auth:
            self.register([UserModel, Group])

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r})"

    def check(self, app_configs):
        """
        Run the system checks on all ModelAdmins, except if they aren't
        customized at all.
        """
        if app_configs is None:
            app_configs = apps.get_app_configs()
        app_configs = set(app_configs)  # Speed up lookups below

        errors = []
        model_admins = (
            o for o in self._registry.values() if o.__class__ is not APIModelAdmin
        )
        for model_admin in model_admins:
            if model_admin.model._meta.app_config in app_configs:
                errors.extend(model_admin.check())
        return errors

    @property
    def actions(self):
        """
        Get all the enabled actions as an iterable of (name, func).
        """
        return self._actions.items()

    def register(self, model_or_iterable, admin_class=None, **options):
        admin_class = admin_class or self.admin_class

        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]

        for model in model_or_iterable:
            if model._meta.abstract:
                raise ImproperlyConfigured(
                    'The model %s is abstract, so it cannot be registered with admin.' % model.__name__
                )

            if model in self._registry:
                raise AlreadyRegistered(
                    'The model %s is already registered ' % model.__name__)

            if not model._meta.swapped:
                if options:
                    options['__module__'] = __name__
                    admin_class = type("%sAPIAdmin" %
                                       model.__name__, (admin_class,), options)

                # Instantiate the admin class to save in the registry
                self._registry[model] = admin_class(model, self)

    def unregister(self, model_or_iterable):
        """
        Unregister the given model(s).

        If a model isn't already registered, raise NotRegistered.
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                raise NotRegistered(
                    "The model %s is not registered" % model.__name__)
            del self._registry[model]

    def is_registered(self, model):
        """
        Check if a model class is registered with this `AdminSite`.
        """
        return model in self._registry

    def get_model_admin(self, model):
        try:
            return self._registry[model]
        except KeyError:
            raise NotRegistered(
                f"The model {model.__name__} is not registered.")

    def has_permission(self, request):
        """
        Return True if the given HttpRequest has permission to view
        *at least one* page in the admin site.
        """
        return request.user.is_active and request.user.is_staff

    def admin_view(self, view, cacheable=False):
        """
        Decorator to create an admin view attached to this ``AdminSite``. This
        wraps the view and provides permission checking by calling
        ``self.has_permission``.

        You'll want to use this from within ``AdminSite.get_urls()``:

            class MyAdminSite(AdminSite):

                def get_urls(self):
                    from django.urls import path

                    urls = super().get_urls()
                    urls += [
                        path('my_view/', self.admin_view(some_view))
                    ]
                    return urls

        By default, admin_views are marked non-cacheable using the
        ``never_cache`` decorator. If the view can be safely cached, set
        cacheable=True.
        """

        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                raise PermissionDenied()

            return view(request, *args, **kwargs)

        if not cacheable:
            inner = never_cache(inner)
        # We add csrf_protect here so this function can be used as a utility
        # function for any view, without having to repeat 'csrf_protect'.
        if not getattr(view, "csrf_exempt", False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    def get_urls(self):

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        urlpatterns = [
            path('', wrap(self.get_app_list_view()), name='index'),
            path('password_change/', wrap(self.get_password_change_view()),
                 name='password_change'),
            path('autocomplete/', wrap(self.autocomplete_view()),
                 name='autocomplete'),
            path('jsoni18n/', wrap(self.get_i18n_javascript_view()),
                 name='language_catalog'),
            path('site_context/', wrap(self.get_site_context_view()),
                 name='site_context'),
            path('admin_log/', wrap(self.get_admin_log_view()),
                 name='admin_log'),
            path('permissions/', wrap(self.get_permissions_view()),
                 name='permissions'),
            path('r/<path:content_type_id>/<path:object_id>/',
                 wrap(self.get_view_on_site_view()), name='view_on_site',),
        ]

        # Add the swagger-ui view
        if self.include_swagger_ui_view:
            urlpatterns.append(path('schema/swagger-ui/',
                                    self.get_docs_view(),
                                    name="swagger-ui"))

        # Save these urls under site_urls for schema tagging
        self.site_urls = copy(urlpatterns)

        # Add in each model's views, and create a list of valid URLS for the
        # app_index
        valid_app_labels = []
        for model, model_admin in self._registry.items():
            self.admin_urls[model] = model_admin.urls
            for url in model_admin.urls:
                urlpatterns += [url]
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

        # If there were ModelAdmins registered, we should have a list of app
        # labels for which we need to allow access to the app_index view,
        if valid_app_labels:
            regex = r"^(?P<app_label>" + "|".join(valid_app_labels) + ")/$"
            app_index_path = re_path(regex, wrap(
                self.get_app_index_view()), name="app_index")
            urlpatterns += [app_index_path]
            self.site_urls += [app_index_path]

        # Add the OpenAPI schema url and update the site_urls
        schema_path = path('schema/', self.get_schema_view(
            [path(f"{self.url_prefix}/", include(urlpatterns))]), name='schema')
        urlpatterns.append(schema_path)
        self.site_urls.append(schema_path)

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.name, self.name

    def _build_app_dict(self, request, label=None):
        """
        Build the app dictionary. The optional `label` parameter filters models
        of a specific app.
        """
        app_dict = {}

        if label:
            models = {
                m: m_a for m, m_a in self._registry.items()
                if m._meta.app_label == label
            }
        else:
            models = self._registry

        for model, model_admin in models.items():
            app_label = model._meta.app_label

            has_module_perms = model_admin.has_module_permission(request)
            if not has_module_perms:
                continue

            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True not in perms.values():
                continue

            info = (self.name, app_label, model._meta.model_name)
            model_dict = {
                'name': capfirst(model._meta.verbose_name_plural),
                'object_name': model._meta.object_name,
                'perms': perms,
                'list_url': None,
                'changelist_url': None,
                'add_url': None,
                'perform_action_url': None,
            }

            if perms.get('change') or perms.get('view'):
                model_dict['view_only'] = not perms.get('change')
                try:
                    model_dict['list_url'] = request.build_absolute_uri(
                        reverse('%s:%s_%s_list' % info, current_app=self.name))
                    model_dict['changelist_url'] = request.build_absolute_uri(
                        reverse('%s:%s_%s_changelist' % info, current_app=self.name))
                    model_dict['perform_action_url'] = request.build_absolute_uri(
                        reverse('%s:%s_%s_perform_action' % info, current_app=self.name))
                except NoReverseMatch:
                    pass

            if perms.get('add'):
                try:
                    model_dict['add_url'] = request.build_absolute_uri(
                        reverse('%s:%s_%s_add' % info, current_app=self.name))
                except NoReverseMatch:
                    pass

            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': apps.get_app_config(app_label).verbose_name,
                    'app_label': app_label,
                    'app_url': reverse(
                        f'{self.name}:app_index',
                        kwargs={'app_label': app_label},
                        current_app=self.name,
                    ),
                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                }

        if label:
            return app_dict.get(label)
        return app_dict

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request, app_label)

        # Sort the apps alphabetically.
        app_list = sorted(app_dict.values(), key=lambda x: x["name"].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app["models"].sort(key=lambda x: x["name"])

        return app_list

    def each_context(self, request):
        """
        Return a dictionary of variables to put in the template context for
        *every* page in the admin site.

        For sites running on a subpath, use the SCRIPT_NAME value if site_url
        hasn't been customized.
        """
        script_name = request.META["SCRIPT_NAME"]
        site_url = (
            script_name if self.site_url == "/" and script_name else self.site_url
        )
        return {
            "site_title": self.site_title,
            "site_header": self.site_header,
            "site_url": site_url,
            "has_permission": request.user.is_active and request.user.is_staff,
            "available_apps": self.get_app_list(request),
            "is_nav_sidebar_enabled": self.enable_nav_sidebar,
        }

    def paginate_queryset(self, queryset, request, view=None):
        paginator = self.default_pagination_class()
        return paginator.paginate_queryset(queryset.order_by('pk'), request, view=view)

    def get_log_entry_serializer(self):
        return type('LogEntrySerializer', (self.log_entry_serializer,), {
            'user': self.user_serializer(read_only=True),
        })

    def get_authentication_classes(self):
        """
        Returns the authentication classes used by the views
        """
        return self.authentication_classes

    def get_app_list_view(self):
        from django_api_admin.admin_views.admin_site_views.app_list import AppListView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self
        }
        return AppListView.as_view(**defaults)

    def get_app_index_view(self):
        from django_api_admin.admin_views.admin_site_views.app_index import AppIndexView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self
        }
        return AppIndexView.as_view(**defaults)

    def get_password_change_view(self):
        from django_api_admin.admin_views.admin_site_views.password_change import PasswordChangeView

        defaults = {
            'serializer_class': self.password_change_serializer,
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self,
        }
        return PasswordChangeView.as_view(**defaults)

    def get_i18n_javascript_view(self):
        from django_api_admin.admin_views.admin_site_views.language_catalog import LanguageCatalogView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self,
        }
        return LanguageCatalogView.as_view(**defaults)

    def autocomplete_view(self):
        from django_api_admin.admin_views.admin_site_views.autocomplete import AutoCompleteView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self
        }
        return AutoCompleteView.as_view(**defaults)

    def get_site_context_view(self):
        from django_api_admin.admin_views.admin_site_views.site_context import SiteContextView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self
        }
        return SiteContextView.as_view(**defaults)

    def get_admin_log_view(self):
        from django_api_admin.admin_views.admin_site_views.admin_log import AdminLogView

        defaults = {
            'pagination_class': self.default_log_pagination_class,
            'serializer_class': self.get_log_entry_serializer(),
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self
        }
        return AdminLogView.as_view(**defaults)

    def get_view_on_site_view(self):
        from django_api_admin.admin_views.admin_site_views.view_on_site import ViewOnSiteView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self,
        }
        return ViewOnSiteView.as_view(**defaults)

    def get_permissions_view(self):
        from django_api_admin.admin_views.admin_site_views.get_permissions import PermissionsView

        defaults = {
            'authentication_classes': self.get_authentication_classes(),
            'admin_site': self
        }
        return PermissionsView.as_view(**defaults)

    def get_schema_view(self, urlconf):
        from drf_spectacular.views import SpectacularAPIView

        return SpectacularAPIView.as_view(urlconf=urlconf)

    def get_docs_view(self):
        from drf_spectacular.views import SpectacularSwaggerView

        return SpectacularSwaggerView.as_view(url_name=f'{self.name}:schema')


class DefaultAdminSite(LazyObject):
    def _setup(self):
        AdminSiteClass = import_string(
            apps.get_app_config("django_api_admin").default_site)
        self._wrapped = AdminSiteClass(name='admin')

    def __repr__(self):
        return repr(self._wrapped)


site = DefaultAdminSite()
