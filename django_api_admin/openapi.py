from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter
from django_api_admin.serializers import EmptyResponseSerializer, ValidationErrorSerializer


form_with_inlines_description = {
    "form": {
        "model": "example.author",
        "readonly_fields": ["date_joined", "is_old_enough"],
        "fields": [
            {
                "type": "CharField",
                "name": "name",
                "attrs": {
                    "read_only": False,
                    "write_only": False,
                    "required": True,
                    "default": None,
                    "allow_null": False,
                    "label": "Name",
                    "help_text": "This is a custom help text for all CharFields",
                    "initial": "",
                    "style": {},
                    "max_length": 100,
                    "min_length": None,
                    "allow_blank": False,
                    "trim_whitespace": True,
                    "current_value": "Muhammad Salah",
                },
            }
        ],
        "fieldsets": [
            [
                "Information",
                {"fields": [["name", "age"], "is_vip", "user", "publisher", "is_old_enough", "date_joined", "location"]},
            ]
        ],
        "prepopulated": {},
        "permissions": {
            "has_add_permission": True,
            "has_change_permission": True,
            "has_delete_permission": True,
            "has_view_permission": True,
        },
        "save_as": False,
        "save_as_continue": True,
        "save_on_top": False,
        "filter_horizontal": [],
        "filter_vertical": [],
        "raw_id_fields": ["publisher"],
        "radio_fields": {},
        "view_on_site": True,
        "autocomplete_fields": ["publisher"],
    },
    "inlines": [
        {
            "model": "example.book",
            "readonly_fields": [],
            "fieldsets": [[None, {"fields": ["id", "title", "author", "credits"]}]],
            "prepopulated": {},
            "permissions": {
                "has_add_permission": True,
                "has_change_permission": True,
                "has_delete_permission": True,
                "has_view_permission": True,
            },
            "extra": 3,
            "min_num": 1,
            "max_num": 4,
            "verbose_name": "book",
            "verbose_name_plural": "books",
            "can_delete": True,
            "show_change_link": False,
            "admin_style": "tabular",
            "formset": [
                [
                    {
                        "type": "CharField",
                        "name": "title",
                        "attrs": {
                            "read_only": False,
                            "write_only": False,
                            "required": True,
                            "default": None,
                            "allow_null": False,
                            "label": "Title",
                            "help_text": None,
                            "initial": "",
                            "style": {},
                            "max_length": 100,
                            "min_length": None,
                            "allow_blank": False,
                            "trim_whitespace": True,
                            "current_value": "How to do something",
                        },
                    }
                ]
            ],
        }
    ],
}


class APIResponseExamples:
    """
    Provides an example of a successful API response for retrieving form field
    """

    @staticmethod
    def form_description():
        return OpenApiExample(
            name=_("Success Response"),
            summary=_("Example of a successful field attribute response"),
            description=_("Retrieve form field attributes for the endpoint"),
            value=form_with_inlines_description,
            status_codes=["200"],
        )

    @staticmethod
    def history_view_200():
        return OpenApiExample(
            name=_("Success Response"),
            value={
                "pagination": {"num_pages": 1, "count": 1, "has_next": False, "has_previous": False},
                "results": [
                    {
                        "id": 1,
                        "user": {
                            "id": 1,
                            "permissions": [
                                "django_api_admin.add_logentry",
                                "example.change_person",
                                "auth.delete_user",
                                "socialaccount.view_socialaccount",
                                "example.delete_publisher",
                                "contenttypes.change_contenttype",
                                "contenttypes.view_contenttype",
                                "example.delete_category",
                                "admin.add_logentry",
                                "example.delete_job",
                                "socialaccount.add_socialtoken",
                                "account.view_emailconfirmation",
                                "example.change_author",
                                "account.change_emailconfirmation",
                                "socialaccount.view_socialapp",
                                "socialaccount.change_socialapp",
                                "example.delete_person",
                                "example.view_person",
                                "example.add_article",
                                "mfa.change_authenticator",
                                "auth.add_permission",
                                "example.change_guestentry",
                                "contenttypes.add_contenttype",
                                "socialaccount.add_socialaccount",
                                "socialaccount.change_socialtoken",
                                "sessions.view_session",
                                "admin.view_logentry",
                                "example.view_publisher",
                                "account.change_emailaddress",
                                "example.view_guestentry",
                                "example.change_revision",
                                "account.delete_emailaddress",
                                "socialaccount.change_socialaccount",
                                "django_api_admin.view_logentry",
                                "example.change_category",
                                "example.delete_book",
                                "account.add_emailaddress",
                                "django_api_admin.change_logentry",
                                "socialaccount.delete_socialtoken",
                                "example.view_product",
                                "sessions.add_session",
                                "account.view_emailaddress",
                                "sessions.change_session",
                                "auth.view_permission",
                                "socialaccount.delete_socialapp",
                                "auth.delete_group",
                                "example.change_article",
                                "example.view_revision",
                                "example.delete_product",
                                "account.add_emailconfirmation",
                                "example.delete_author",
                                "example.add_person",
                                "example.add_publisher",
                                "socialaccount.view_socialtoken",
                                "auth.view_user",
                                "example.add_job",
                                "account.delete_emailconfirmation",
                                "example.add_product",
                                "django_api_admin.delete_logentry",
                                "example.delete_article",
                                "auth.delete_permission",
                                "auth.add_user",
                                "example.add_book",
                                "example.delete_revision",
                                "example.view_job",
                                "example.add_author",
                                "socialaccount.delete_socialaccount",
                                "admin.change_logentry",
                                "example.change_publisher",
                                "mfa.delete_authenticator",
                                "auth.change_user",
                                "example.delete_guestentry",
                                "example.view_article",
                                "example.change_book",
                                "mfa.view_authenticator",
                                "admin.delete_logentry",
                                "example.add_revision",
                                "contenttypes.delete_contenttype",
                                "auth.change_group",
                                "auth.change_permission",
                                "example.view_author",
                                "example.change_job",
                                "auth.view_group",
                                "example.change_product",
                                "example.view_book",
                                "auth.add_group",
                                "example.add_category",
                                "socialaccount.add_socialapp",
                                "example.add_guestentry",
                                "sessions.delete_session",
                                "mfa.add_authenticator",
                                "example.view_category",
                            ],
                            "last_login": "2026-05-06T13:20:22.418291Z",
                            "is_superuser": True,
                            "username": "ms",
                            "first_name": "",
                            "last_name": "",
                            "email": "ms@email.com",
                            "is_staff": True,
                            "is_active": True,
                            "date_joined": "2026-01-27T21:01:04Z",
                            "groups": [],
                            "user_permissions": [],
                        },
                        "action_time": "2026-04-24T10:32:53.511990Z",
                        "object_id": "1",
                        "object_repr": "Muhammad Salah",
                        "action_flag": 2,
                        "change_message": [{"changed": {"fields": ["Age"]}}],
                        "content_type": 8,
                    }
                ],
            },
            status_codes=["200"],
        )


class CommonAPIResponses:
    """Collection of standardized OpenAPI response templates."""

    @staticmethod
    def permission_denied():
        return OpenApiResponse(
            description=_("Forbidden"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("Permission denied"),
                    value={"status": 403},
                    status_codes=["403"],
                )
            ],
        )

    @staticmethod
    def ok(message=None):
        return OpenApiResponse(
            description=_(message or "OK"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("OK"),
                    value={"status": 200},
                    status_codes=["200"],
                )
            ],
        )

    @staticmethod
    def not_found():
        return OpenApiResponse(
            description=_("Resource not found"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("Not Found"),
                    value={"status": 404},
                    status_codes=["404"],
                )
            ],
        )

    @staticmethod
    def bad_request():
        return OpenApiResponse(
            description=_("Bad request"),
            response=ValidationErrorSerializer,
            examples=[
                OpenApiExample(
                    name=_("Bad Request"),
                    value={"status": 400, "errors": [{"message": "This field is required.", "param": "pk"}]},
                    status_codes=["400"],
                )
            ],
        )

    @staticmethod
    def unauthorized():
        return OpenApiResponse(
            description=_("Not authenticated"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("Unauthorized"),
                    value={"status": 401},
                    status_codes=["401"],
                )
            ],
        )

    @staticmethod
    def method_not_allowed():
        return OpenApiResponse(
            description=_("Method not allowed"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("Method Not Allowed"),
                    value={"status": 405},
                    status_codes=["405"],
                )
            ],
        )

    @staticmethod
    def conflict():
        return OpenApiResponse(
            description=_("Resource conflict"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("Conflict"),
                    value={"status": 409},
                    status_codes=["409"],
                )
            ],
        )

    @staticmethod
    def server_error():
        return OpenApiResponse(
            description=_("Internal server error"),
            response=EmptyResponseSerializer,
            examples=[
                OpenApiExample(
                    name=_("Server Error"),
                    value={"status": 500},
                    status_codes=["500"],
                )
            ],
        )


class CommonAPIQueryParams:
    page = OpenApiParameter(
        name="page",
        type=int,
        default=1,
        location=OpenApiParameter.QUERY,
        description=_("A page number within the paginated result set."),
    )
    to_field = OpenApiParameter(
        name="_to_field",
        type=str,
        location=OpenApiParameter.QUERY,
        description=_("The field to match for lookups."),
        required=False,
    )


class CommonAPIPathParams:
    object_id = OpenApiParameter(
        name="object_id",
        type=str,
        location=OpenApiParameter.PATH,
        description=_("The primary key value of the instance to be updated"),
        required=True,
    )


user = {
    "id": 1,
    "last_login": "2025-01-25T13:00:49.925221Z",
    "is_superuser": True,
    "username": "ms",
    "first_name": "Muhammad",
    "last_name": "Salah",
    "email": "ms@email.com",
    "is_staff": True,
    "is_active": True,
    "date_joined": "2025-01-24T11:43:43.500792Z",
    "groups": [],
    "user_permissions": [],
}

change_list = {
    "status": 200,
    "data": {
        "action_form": {
            "fields": [
                {
                    "type": "ChoiceField",
                    "name": "action",
                    "attrs": {
                        "read_only": False,
                        "write_only": False,
                        "required": True,
                        "default": None,
                        "allow_null": False,
                        "label": "Action",
                        "help_text": None,
                        "initial": None,
                        "style": {},
                        "choices": {
                            "": "---------",
                            "delete_selected": "Delete selected authors",
                            "make_old": "make all authors old",
                            "make_young": "make all authors young",
                        },
                        "allow_blank": False,
                        "html_cutoff": None,
                        "html_cutoff_text": "More than {count} items...",
                    },
                },
            ]
        },
        "config": {
            "actions_on_top": True,
            "actions_on_bottom": False,
            "actions_selection_counter": True,
            "empty_value_display": "-",
            "list_display": ["name", "age", "user", "is_old_enough", "title", "gender"],
            "list_display_links": ["name"],
            "list_editable": ["title"],
            "exclude": ["gender"],
            "show_full_result_count": True,
            "list_per_page": 6,
            "list_max_show_all": 200,
            "date_hierarchy": "date_joined",
            "search_help_text": None,
            "sortable_by": None,
            "search_fields": ["name", "publisher__name"],
            "preserve_filters": True,
            "full_count": 1,
            "result_count": 1,
            "action_choices": [
                ["delete_selected", "Delete selected authors"],
                ["make_old", "make all authors old"],
                ["make_young", "make all authors young"],
            ],
            "filters": [
                {
                    "title": "is vip",
                    "choices": [
                        {"selected": True, "query_string": "?", "display": "All"},
                        {"selected": False, "query_string": "?is_vip__exact=1", "display": "Yes"},
                        {"selected": False, "query_string": "?is_vip__exact=0", "display": "No"},
                    ],
                },
                {
                    "title": "age",
                    "choices": [
                        {"selected": True, "query_string": "?", "display": "All"},
                        {"selected": False, "query_string": "?age__exact=60", "display": "senior"},
                        {"selected": False, "query_string": "?age__exact=1", "display": "baby"},
                        {"selected": False, "query_string": "?age__exact=2", "display": "also a baby"},
                    ],
                },
            ],
            "list_display_fields": ["name", "age", "user", "title"],
            "editing_fields": [
                {
                    "type": "CharField",
                    "name": "title",
                    "attrs": {
                        "read_only": False,
                        "write_only": False,
                        "required": False,
                        "default": None,
                        "allow_blank": False,
                        "allow_null": True,
                        "style": {},
                        "label": "Title",
                        "help_text": None,
                        "initial": "",
                        "max_length": 20,
                        "min_length": None,
                        "trim_whitespace": True,
                    },
                }
            ],
        },
        "columns": [
            {"field": "name", "headerName": "name"},
            {"field": "age", "headerName": "age"},
            {"field": "user", "headerName": "user"},
            {"field": "is_old_enough", "headerName": "is this author old enough"},
            {"field": "title", "headerName": "title"},
        ],
        "rows": [
            {
                "id": 1,
                "cells": {"name": "Muhammad", "age": "60", "user": "ms", "is_old_enough": True, "title": "-"},
            }
        ],
    },
}

crud_operation = {
    "detail": "The author “René Descartes” was changed successfully.",
    "data": {
        "id": 1,
        "name": "Renene Descartes",
        "age": 60,
        "is_vip": True,
        "date_joined": "2025-02-05T04:12:12.191849Z",
        "title": None,
        "user": 1,
        "publisher": [1],
        "pk": 1,
    },
}

site_context = {
    "site_title": "Django site admin",
    "site_header": "Django administration",
    "site_url": "/",
    "has_permission": True,
    "available_apps": [
        {
            "name": "Authentication and Authorization",
            "app_label": "auth",
            "app_url": "/api_admin/auth/",
            "has_module_perms": True,
            "models": [
                {
                    "name": "Users",
                    "object_name": "User",
                    "perms": {"add": True, "change": True, "delete": True, "view": True},
                }
            ],
        }
    ],
    "is_nav_sidebar_enabled": True,
}
