from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from django_api_admin.models import LogEntry

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        exclude = ("password",)

    def get_permissions(self, obj):
        return list(obj.get_all_permissions())


class LogEntrySerializer(serializers.ModelSerializer):
    """
    default LogEntry serializer.
    """
    class Meta:
        model = LogEntry
        fields = "__all__"
        extra_kwargs = {
            "action_time": {"help_text": _("The date and time of the action.")},
            "user": {"help_text": _("The user who performed the action.")},
            "content_type": {"help_text": _("The content type of the object being acted upon.")},
            "object_id": {"help_text": _("The ID of the object being acted upon.")},
            "object_repr": {"help_text": _("The textual representation of the object.")},
            "action_flag": {"help_text": _("The type of action (1 for Addition, 2 for Change, 3 for Deletion).")},
            "change_message": {"help_text": _("A description of the changes made.")},
        }


class PaginationSerializer(serializers.Serializer):
    num_pages = serializers.IntegerField(
        required=True, help_text=_("The total number of pages."))
    count = serializers.IntegerField(
        required=True, help_text=_("The total number of items."))
    has_next = serializers.BooleanField(
        required=True, help_text=_("Whether there is a next page."))
    has_previous = serializers.BooleanField(
        required=True, help_text=_("Whether there is a previous page."))


class HistoryViewResponseSerializer(serializers.Serializer):
    pagination = PaginationSerializer(
        required=True, help_text=_("Pagination information."))
    results = LogEntrySerializer(
        many=True, required=True, help_text=_("the list of log entries."))


class HistoryViewRequestSerializer(serializers.Serializer):
    """
    Serializer for the admin log request.
    """
    o = serializers.ChoiceField(
        choices=[
            ("action_time", "Action Time (Ascending)"),
            ("-action_time", "Action Time (Descending)")
        ],
        required=False,
        help_text=_("The field to use for ordering the log entries.")
    )
    object_id = serializers.IntegerField(
        required=False,
        help_text=_("The ID of the specific object to filter logs for.")
    )


class PasswordChangeSerializer(serializers.Serializer):
    """
    Allow changing password by entering the old_password and a new one.
    """
    old_password = serializers.CharField(
        label=_("Old password"),
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )
    new_password1 = serializers.CharField(
        label=_("New Password"),
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        label=_("New password confirmation"),
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.error_messages.update({
            "password_mismatch": _("The two password fields didn’t match."),
            "password_incorrect": _("Your old password was entered incorrectly. Please enter it again."),
        })

    def validate(self, data):
        user = self.context["user"]

        old_password = data["old_password"]
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )

        password1 = data.get("new_password1")
        password2 = data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise serializers.ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch"
            )

        return data

    def save(self, commit=True):
        password = self.validated_data["new_password1"]
        user = self.context["user"]
        user.set_password(password)
        if commit:
            user.save()
        return user


class ActionSerializer(serializers.Serializer):
    """
    checks that a valid action is selected
    """
    action = serializers.ChoiceField(choices=[("", "---------"), ])
    selected_ids = serializers.MultipleChoiceField(choices=[("", "")])
    select_across = serializers.BooleanField(required=False, default=0)


class ChangeListSerializer(serializers.Serializer):
    """
    Validates the changelist querystring
    """
    q = serializers.CharField(required=False, trim_whitespace=False)
    p = serializers.IntegerField(required=False, min_value=1)
    all = serializers.BooleanField(required=False)
    o = serializers.CharField(required=False)
    _to_field = serializers.CharField(required=False)


class AppIndexSerializer(serializers.Serializer):
    app_label = serializers.CharField()

    def validate(self, attrs):
        if attrs["app_label"] not in self.context["registered_app_labels"]:
            raise serializers.ValidationError(
                _("finish must occur after start"))
        return super().validate(attrs)


class PermissionsSerializer(serializers.Serializer):
    add = serializers.BooleanField(
        help_text=_("Whether the user can add objects."))
    change = serializers.BooleanField(
        help_text=_("Whether the user can change objects."))
    delete = serializers.BooleanField(
        help_text=_("Whether the user can delete objects."))
    view = serializers.BooleanField(
        help_text=_("Whether the user can view objects."))


class ModelSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("The name of the model."))
    object_name = serializers.CharField(
        help_text=_("The name of instances of that model."))
    perms = PermissionsSerializer(
        help_text=_("The permissions for the model."))
    view_only = serializers.BooleanField(
        help_text=_("Whether the model is view-only."))


class AppSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("The name of the application."))
    app_label = serializers.CharField(
        help_text=_("The label of the application."))
    app_url = serializers.CharField(help_text=_("The URL of the application."))
    has_module_perms = serializers.BooleanField(
        help_text=_("Whether the user has permissions for this application."))
    models = ModelSerializer(
        many=True, help_text=_("The list of models in this application."))


class AppListSerializer(serializers.Serializer):
    app_list = AppSerializer(
        many=True, help_text=_("The list of registered applications."))


class AutoCompleteSerializer(serializers.Serializer):
    app_label = serializers.CharField(
        required=True,
        help_text=_("The app label of the model to search.")
    )
    model_name = serializers.CharField(
        required=True,
        help_text=_("The name of the model to search.")
    )
    field_name = serializers.CharField(
        required=True,
        help_text=_("The name of the source field to use for the search.")
    )
    term = serializers.CharField(
        required=False,
        default="",
        help_text=_("The search term to filter results.")
    )


class AutocompleteResultSerializer(serializers.Serializer):
    id = serializers.CharField(help_text=_(
        "The unique identifier of the object."))
    text = serializers.CharField(
        help_text=_("The display text of the object."))


class AutocompletePaginationSerializer(serializers.Serializer):
    more = serializers.BooleanField(help_text=_(
        "Whether more results are available."))


class AutocompleteResponseSerializer(serializers.Serializer):
    results = AutocompleteResultSerializer(
        many=True, help_text=_("The list of search results."))
    pagination = AutocompletePaginationSerializer(
        help_text=_("Pagination information."))


class FormatsSerializer(serializers.Serializer):
    DATE_FORMAT = serializers.CharField(allow_blank=False)
    DATETIME_FORMAT = serializers.CharField(allow_blank=False)
    TIME_FORMAT = serializers.CharField(allow_blank=False)
    YEAR_MONTH_FORMAT = serializers.CharField(allow_blank=False)
    MONTH_DAY_FORMAT = serializers.CharField(allow_blank=False)
    SHORT_DATE_FORMAT = serializers.CharField(allow_blank=False)
    SHORT_DATETIME_FORMAT = serializers.CharField(allow_blank=False)
    FIRST_DAY_OF_WEEK = serializers.IntegerField()
    DECIMAL_SEPARATOR = serializers.CharField(allow_blank=False)
    THOUSAND_SEPARATOR = serializers.CharField(allow_blank=False)
    NUMBER_GROUPING = serializers.IntegerField()
    DATE_INPUT_FORMATS = serializers.ListField(
        child=serializers.CharField(allow_blank=False)
    )
    TIME_INPUT_FORMATS = serializers.ListField(
        child=serializers.CharField(allow_blank=False)
    )
    DATETIME_INPUT_FORMATS = serializers.ListField(
        child=serializers.CharField(allow_blank=False)
    )


class FieldAttributesSerializer(serializers.Serializer):
    read_only = serializers.BooleanField(default=False)
    write_only = serializers.BooleanField(default=False)
    required = serializers.BooleanField(default=True)
    default = serializers.CharField(allow_null=True, required=False)
    allow_blank = serializers.BooleanField(default=False)
    allow_null = serializers.BooleanField(default=False)
    style = serializers.JSONField(default=dict)
    label = serializers.CharField(allow_null=True, required=False)
    help_text = serializers.CharField(allow_null=True, required=False)
    initial = serializers.CharField(default="", required=False)
    max_length = serializers.IntegerField(allow_null=True, required=False)
    min_length = serializers.IntegerField(allow_null=True, required=False)
    trim_whitespace = serializers.BooleanField(default=True)
    min_value = serializers.FloatField(allow_null=True, required=False)
    max_value = serializers.FloatField(allow_null=True, required=False)
    format = serializers.CharField(allow_null=True, required=False)
    input_formats = serializers.ListField(
        child=serializers.CharField(allow_null=True, required=False)
    )
    choices = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField()
        )
    )
    html_cutoff = serializers.IntegerField()
    html_cutoff_text = serializers.CharField()
    allow_empty_files = serializers.BooleanField()
    use_url = serializers.BooleanField()
    allow_empty = serializers.BooleanField()
    child = serializers.JSONField()


class FieldSerializer(serializers.Serializer):
    type = serializers.CharField()
    name = serializers.CharField()
    attrs = FieldAttributesSerializer()


class FormFieldsSerializer(serializers.Serializer):
    fields = FieldSerializer(many=True)


class URLsSerializer(serializers.Serializer):
    url = serializers.URLField()


class APIRootSerializer(serializers.Serializer):
    urls = URLsSerializer(many=True)


class TokensSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class ObtainTokenResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    user = UserSerializer()
    tokens = TokensSerializer()


class SiteContextSerializer(serializers.Serializer):
    site_title = serializers.CharField(
        help_text=_("The title of the admin site."))
    site_header = serializers.CharField(
        help_text=_("The header of the admin site."))
    site_url = serializers.CharField(help_text=_("The URL of the admin site."))
    has_permission = serializers.BooleanField(
        help_text=_("Whether the user has permission to access the site."))
    available_apps = AppSerializer(
        many=True, help_text=_("The list of applications available to the user."))
    is_nav_siderbar_enabled = serializers.BooleanField(
        help_text=_("Whether the navigation sidebar is enabled."))


class ActionChoiceSerializer(serializers.Serializer):
    action = serializers.CharField()
    description = serializers.CharField()


class FilterChoiceSerializer(serializers.Serializer):
    selected = serializers.BooleanField()
    query_string = serializers.CharField()
    display = serializers.CharField()


class FilterSerializer(serializers.Serializer):
    title = serializers.CharField()
    choices = FilterChoiceSerializer(many=True)


class EditingFieldSerializer(serializers.Serializer):
    type = serializers.CharField()
    name = serializers.CharField()
    attrs = serializers.DictField()


class ConfigSerializer(serializers.Serializer):
    actions_on_top = serializers.BooleanField()
    actions_on_bottom = serializers.BooleanField()
    actions_selection_counter = serializers.BooleanField()
    empty_value_display = serializers.CharField()
    list_display = serializers.ListField(child=serializers.CharField())
    list_display_links = serializers.ListField(child=serializers.CharField())
    list_editable = serializers.ListField(child=serializers.CharField())
    exclude = serializers.ListField(child=serializers.CharField())
    show_full_result_count = serializers.BooleanField()
    list_per_page = serializers.IntegerField()
    list_max_show_all = serializers.IntegerField()
    date_hierarchy = serializers.CharField()
    search_help_text = serializers.CharField(allow_null=True)
    sortable_by = serializers.ListField(
        child=serializers.CharField(), allow_null=True)
    search_fields = serializers.ListField(child=serializers.CharField())
    preserve_filters = serializers.BooleanField()
    full_count = serializers.IntegerField()
    result_count = serializers.IntegerField()
    action_choices = ActionChoiceSerializer(many=True)
    filters = FilterSerializer(many=True)
    list_display_fields = serializers.ListField(child=serializers.CharField())
    editing_fields = serializers.ListField(child=EditingFieldSerializer())


class ColumnSerializer(serializers.Serializer):
    field = serializers.CharField()
    headerName = serializers.CharField()


class CellSerializer(serializers.Serializer):
    name = serializers.CharField()
    age = serializers.CharField()
    user = serializers.CharField()
    is_old_enough = serializers.BooleanField()
    title = serializers.CharField()


class RowSerializer(serializers.Serializer):
    change_url = serializers.URLField()
    id = serializers.IntegerField()
    cells = CellSerializer()


class ChangelistResponseSerializer(serializers.Serializer):
    action_form = FormFieldsSerializer()
    config = ConfigSerializer()
    columns = ColumnSerializer(many=True)
    rows = RowSerializer(many=True)


class BulkUpdatesResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    updated_inlines = serializers.ListField(child=serializers.DictField())
    deleted_inlines = serializers.ListField(child=serializers.DictField())


class ResponseMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ErrorMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()
