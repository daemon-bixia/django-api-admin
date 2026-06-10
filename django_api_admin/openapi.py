from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter
from django_api_admin.serializers import (
    OKResponseSerializer,
    ValidationErrorSerializer,
    PermissionDeniedResponseSerializer,
    NotFoundResponseSerializer,
    UnauthorizedResponseSerializer,
    MethodNotAllowedResponseSerializer,
    ConflictResponseSerializer,
    ServerErrorResponseSerializer,
)


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
            value={"status": 200, "data": form_with_inlines_description},
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
    def ok(description=None):
        return OpenApiResponse(
            description=_(description or "OK"),
            response=OKResponseSerializer,
        )

    @staticmethod
    def permission_denied(description=None):
        return OpenApiResponse(
            description=_(description or "Forbidden"),
            response=PermissionDeniedResponseSerializer,
        )

    @staticmethod
    def not_found(description=None):
        return OpenApiResponse(
            description=_(description or "Resource not found"),
            response=NotFoundResponseSerializer,
        )

    @staticmethod
    def bad_request(description=None):
        return OpenApiResponse(
            description=_(description or "Bad request"),
            response=ValidationErrorSerializer,
        )

    @staticmethod
    def unauthorized(description=None):
        return OpenApiResponse(
            description=_(description or "Not authenticated"),
            response=UnauthorizedResponseSerializer,
        )

    @staticmethod
    def method_not_allowed(description=None):
        return OpenApiResponse(
            description=_(description or "Method not allowed"),
            response=MethodNotAllowedResponseSerializer,
        )

    @staticmethod
    def conflict(description=None):
        return OpenApiResponse(
            description=_(description or "Resource conflict"),
            response=ConflictResponseSerializer,
        )

    @staticmethod
    def server_error(description=None):
        return OpenApiResponse(
            description=_(description or "Internal server error"),
            response=ServerErrorResponseSerializer,
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
