from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter
from django_api_admin.serializers import ErrorMessageSerializer


form_with_inlines_description = {
    "form": {
        "model": "test_django_api_admin.author",
        "readonly_fields": [
            "date_joined",
            "is_old_enough"
        ],
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
                    "current_value": "Muhammad Salah"
                }
            }
        ],
        "fieldsets": [
            [
                "Information",
                {
                    "fields": [
                        ["name", "age"],
                        "is_vip",
                        "user",
                        "publisher",
                        "is_old_enough",
                        "date_joined",
                        "location"
                    ]
                }
            ]
        ],
        "prepopulated": {},
        "permissions": {
            "has_add_permission": True,
            "has_change_permission": True,
            "has_delete_permission": True,
            "has_view_permission": True
        },
        "save_as": False,
        "save_as_continue": True,
        "save_on_top": False,
        "filter_horizontal": [],
        "filter_vertical": [],
        "raw_id_fields": [
            "publisher"
        ],
        "radio_fields": {},
        "view_on_site": True,
        "autocomplete_fields": [
            "publisher"
        ]
    },
    "inlines": [
        {
            "model": "test_django_api_admin.book",
            "readonly_fields": [],
            "fieldsets": [
                [
                    None,
                    {
                        "fields": [
                            "id",
                            "title",
                            "author",
                            "credits"
                        ]
                    }
                ]
            ],
            "prepopulated": {},
            "permissions": {
                "has_add_permission": True,
                "has_change_permission": True,
                "has_delete_permission": True,
                "has_view_permission": True
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
                            "current_value": "How to do something"
                        }
                    }
                ]
            ]
        }
    ]
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
            description=_(
                "Retrieve form field attributes for the endpoint"),
            value=form_with_inlines_description,
            status_codes=["200"],
        )

    @staticmethod
    def history_view_200():
        return OpenApiExample(
            name=_("Success Response"),
            value={
                "pagination": {
                    "num_pages": 1,
                    "count": 1,
                    "has_next": False,
                    "has_previous": False
                },
                "results": [
                    {
                        "id": 1,
                        "user": {
                            "id": 1,
                            "permissions": [
                                "django_api_admin.add_logentry",
                                "test_django_api_admin.change_person",
                                "auth.delete_user",
                                "socialaccount.view_socialaccount",
                                "test_django_api_admin.delete_publisher",
                                "contenttypes.change_contenttype",
                                "contenttypes.view_contenttype",
                                "test_django_api_admin.delete_category",
                                "admin.add_logentry",
                                "test_django_api_admin.delete_job",
                                "socialaccount.add_socialtoken",
                                "account.view_emailconfirmation",
                                "test_django_api_admin.change_author",
                                "account.change_emailconfirmation",
                                "socialaccount.view_socialapp",
                                "socialaccount.change_socialapp",
                                "test_django_api_admin.delete_person",
                                "test_django_api_admin.view_person",
                                "test_django_api_admin.add_article",
                                "mfa.change_authenticator",
                                "auth.add_permission",
                                "test_django_api_admin.change_guestentry",
                                "contenttypes.add_contenttype",
                                "socialaccount.add_socialaccount",
                                "socialaccount.change_socialtoken",
                                "sessions.view_session",
                                "admin.view_logentry",
                                "test_django_api_admin.view_publisher",
                                "account.change_emailaddress",
                                "test_django_api_admin.view_guestentry",
                                "test_django_api_admin.change_revision",
                                "account.delete_emailaddress",
                                "socialaccount.change_socialaccount",
                                "django_api_admin.view_logentry",
                                "test_django_api_admin.change_category",
                                "test_django_api_admin.delete_book",
                                "account.add_emailaddress",
                                "django_api_admin.change_logentry",
                                "socialaccount.delete_socialtoken",
                                "test_django_api_admin.view_product",
                                "sessions.add_session",
                                "account.view_emailaddress",
                                "sessions.change_session",
                                "auth.view_permission",
                                "socialaccount.delete_socialapp",
                                "auth.delete_group",
                                "test_django_api_admin.change_article",
                                "test_django_api_admin.view_revision",
                                "test_django_api_admin.delete_product",
                                "account.add_emailconfirmation",
                                "test_django_api_admin.delete_author",
                                "test_django_api_admin.add_person",
                                "test_django_api_admin.add_publisher",
                                "socialaccount.view_socialtoken",
                                "auth.view_user",
                                "test_django_api_admin.add_job",
                                "account.delete_emailconfirmation",
                                "test_django_api_admin.add_product",
                                "django_api_admin.delete_logentry",
                                "test_django_api_admin.delete_article",
                                "auth.delete_permission",
                                "auth.add_user",
                                "test_django_api_admin.add_book",
                                "test_django_api_admin.delete_revision",
                                "test_django_api_admin.view_job",
                                "test_django_api_admin.add_author",
                                "socialaccount.delete_socialaccount",
                                "admin.change_logentry",
                                "test_django_api_admin.change_publisher",
                                "mfa.delete_authenticator",
                                "auth.change_user",
                                "test_django_api_admin.delete_guestentry",
                                "test_django_api_admin.view_article",
                                "test_django_api_admin.change_book",
                                "mfa.view_authenticator",
                                "admin.delete_logentry",
                                "test_django_api_admin.add_revision",
                                "contenttypes.delete_contenttype",
                                "auth.change_group",
                                "auth.change_permission",
                                "test_django_api_admin.view_author",
                                "test_django_api_admin.change_job",
                                "auth.view_group",
                                "test_django_api_admin.change_product",
                                "test_django_api_admin.view_book",
                                "auth.add_group",
                                "test_django_api_admin.add_category",
                                "socialaccount.add_socialapp",
                                "test_django_api_admin.add_guestentry",
                                "sessions.delete_session",
                                "mfa.add_authenticator",
                                "test_django_api_admin.view_category"
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
                            "user_permissions": []
                        },
                        "action_time": "2026-04-24T10:32:53.511990Z",
                        "object_id": "1",
                        "object_repr": "Muhammad Salah",
                        "action_flag": 2,
                        "change_message": [
                            {
                                "changed": {
                                    "fields": [
                                        "Age"
                                    ]
                                }
                            }
                        ],
                        "content_type": 8
                    }
                ]
            },
            status_codes=["200"],
        )


class CommonAPIResponses:
    """Collection of standardized OpenAPI response templates."""

    @staticmethod
    def permission_denied():
        return OpenApiResponse(
            description=_("Forbidden"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Permission denied"),
                    value={"detail": _(
                        "You do not have permission to perform this action.")},
                    status_codes=["403"]
                )
            ]
        )

    @staticmethod
    def not_found():
        return OpenApiResponse(
            description=_("Resource not found"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Not Found"),
                    value={
                        "detail": _("The requested resource was not found.")
                    },
                    status_codes=["404"]
                )
            ]
        )

    @staticmethod
    def bad_request():
        return OpenApiResponse(
            description=_("Bad request"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Bad Request"),
                    value={
                        "detail": _("The request contains invalid parameters or data.")
                    },
                    status_codes=["400"]
                )
            ]
        )

    @staticmethod
    def unauthorized():
        return OpenApiResponse(
            description=_("Not authenticated"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Unauthorized"),
                    value={"detail": _(
                        "Authentication credentials were not provided.")},
                    status_codes=["401"]
                )
            ]
        )

    @staticmethod
    def method_not_allowed():
        return OpenApiResponse(
            description=_("Method not allowed"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Method Not Allowed"),
                    value={
                        "detail": _("Method not allowed for this endpoint.")
                    },
                    status_codes=["405"]
                )
            ]
        )

    @staticmethod
    def conflict():
        return OpenApiResponse(
            description=_("Resource conflict"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Conflict"),
                    value={
                        "detail": _("The request conflicts with the current state of the target resource.")
                    },
                    status_codes=["409"]
                )
            ]
        )

    @staticmethod
    def server_error():
        return OpenApiResponse(
            description=_("Internal server error"),
            response=ErrorMessageSerializer,
            examples=[
                OpenApiExample(
                    name=_("Server Error"),
                    value={
                        "detail": _("An unexpected error occurred while processing the request.")
                    },
                    status_codes=["500"]
                )
            ]
        )


class CommonAPIQueryParams:
    page = OpenApiParameter(
        name="page",
        type=int,
        default=1,
        location=OpenApiParameter.QUERY,
        description=_("A page number within the paginated result set.")
    )


class CommonAPIPathParams:
    object_id = OpenApiParameter(
        name="object_id",
        type=str,
        location=OpenApiParameter.PATH,
        description=_(
            "The primary key value of the instance to be updated"),
        required=True,
    )


User = {
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
    "user_permissions": []
}

ChangeList = {
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
                            "make_young": "make all authors young"
                        },
                    "allow_blank": False,
                    "html_cutoff": None,
                    "html_cutoff_text": "More than {count} items..."
                }
            },]
    },
    "config": {
        "actions_on_top": True,
        "actions_on_bottom": False,
        "actions_selection_counter": True,
        "empty_value_display": "-",
        "list_display": [
            "name", "age", "user", "is_old_enough", "title", "gender"
        ],
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
            ["make_young", "make all authors young"]
        ],
        "filters": [
            {
                "title": "is vip",
                "choices": [
                    {"selected": True, "query_string": "?", "display": "All"},
                    {"selected": False, "query_string": "?is_vip__exact=1",
                        "display": "Yes"},
                    {"selected": False, "query_string": "?is_vip__exact=0",
                        "display": "No"}
                ]
            },
            {
                "title": "age",
                "choices": [
                    {"selected": True, "query_string": "?", "display": "All"},
                    {"selected": False, "query_string": "?age__exact=60",
                        "display": "senior"},
                    {"selected": False, "query_string": "?age__exact=1",
                        "display": "baby"},
                    {"selected": False, "query_string": "?age__exact=2",
                        "display": "also a baby"}
                ]
            }
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
                    "trim_whitespace": True
                }
            }
        ],
    },
    "columns": [
        {"field": "name", "headerName": "name"},
        {"field": "age", "headerName": "age"},
        {"field": "user", "headerName": "user"},
        {"field": "is_old_enough", "headerName": "is this author old enough"},
        {"field": "title", "headerName": "title"}
    ],
    "rows": [
        {
            "change_url": "http://localhost:8000/api_admin/test_django_api_admin/author/1/change/",
            "id": 1,
            "cells": {
                "name": "Muhammad",
                "age": "60",
                "user": "ms",
                "is_old_enough": True,
                "title": "-"
            }
        }
    ]
}

CrudOperation = {
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
        "pk": 1
    },
}
