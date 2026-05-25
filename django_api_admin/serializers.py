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
            "content_type": {
                "help_text": _("The content type of the object being acted upon.")
            },
            "object_id": {"help_text": _("The ID of the object being acted upon.")},
            "object_repr": {
                "help_text": _("The textual representation of the object.")
            },
            "action_flag": {
                "help_text": _(
                    "The type of action (1 for Addition, 2 for Change, 3 for Deletion)."
                )
            },
            "change_message": {"help_text": _("A description of the changes made.")},
        }


class PaginationSerializer(serializers.Serializer):
    num_pages = serializers.IntegerField(
        required=True, help_text=_("The total number of pages.")
    )
    count = serializers.IntegerField(
        required=True, help_text=_("The total number of items.")
    )
    has_next = serializers.BooleanField(
        required=True, help_text=_("Whether there is a next page.")
    )
    has_previous = serializers.BooleanField(
        required=True, help_text=_("Whether there is a previous page.")
    )


class HistoryViewResponseSerializer(serializers.Serializer):
    pagination = PaginationSerializer(
        required=True, help_text=_("Pagination information.")
    )
    results = LogEntrySerializer(
        many=True, required=True, help_text=_("the list of log entries.")
    )


class HistoryViewRequestSerializer(serializers.Serializer):
    """
    Serializer for the admin log request.
    """

    o = serializers.ChoiceField(
        choices=[
            ("action_time", "Action Time (Ascending)"),
            ("-action_time", "Action Time (Descending)"),
        ],
        required=False,
        help_text=_("The field to use for ordering the log entries."),
    )
    object_id = serializers.IntegerField(
        required=False, help_text=_("The ID of the specific object to filter logs for.")
    )


class ViewOnsiteViewResponseSerializer(serializers.Serializer):
    url = serializers.CharField(
        required=True, help_text=_("The site-specific absolute URL of the object.")
    )


class ActionSerializer(serializers.Serializer):
    """
    checks that a valid action is selected
    """

    action = serializers.ChoiceField(
        choices=[
            ("", "---------"),
        ]
    )
    selected_ids = serializers.MultipleChoiceField(choices=[("", "")])
    select_across = serializers.BooleanField(required=False, default=0)


class ChangeListSerializer(serializers.Serializer):
    """
    Validates the changelist querystring
    """
    q = serializers.CharField(
        required=False, trim_whitespace=False, help_text=_("Search query.")
    )
    p = serializers.IntegerField(
        required=False, min_value=1, help_text=_("Page number.")
    )
    all = serializers.BooleanField(
        required=False, help_text=_("Show all results."))
    o = serializers.CharField(
        required=False, help_text=_("The field(s) to use for ordering.")
    )
    _to_field = serializers.CharField(
        required=False, help_text=_("The field to match for lookups.")
    )


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
        help_text=_("Whether the user can change objects.")
    )
    delete = serializers.BooleanField(
        help_text=_("Whether the user can delete objects.")
    )
    view = serializers.BooleanField(
        help_text=_("Whether the user can view objects."))


class ModelSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("The name of the model."))
    object_name = serializers.CharField(
        help_text=_("The name of instances of that model.")
    )
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
        help_text=_("Whether the user has permissions for this application.")
    )
    models = ModelSerializer(
        many=True, help_text=_("The list of models in this application.")
    )


class AppListSerializer(serializers.Serializer):
    app_list = AppSerializer(
        many=True, help_text=_("The list of registered applications.")
    )


class AutoCompleteSerializer(serializers.Serializer):
    app_label = serializers.CharField(
        required=True, help_text=_("The app label of the model to search.")
    )
    model_name = serializers.CharField(
        required=True, help_text=_("The name of the model to search.")
    )
    field_name = serializers.CharField(
        required=True,
        help_text=_("The name of the source field to use for the search."),
    )
    term = serializers.CharField(
        required=False, default="", help_text=_("The search term to filter results.")
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
        many=True, help_text=_("The list of search results.")
    )
    pagination = AutocompletePaginationSerializer(
        help_text=_("Pagination information.")
    )


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
    read_only = serializers.BooleanField(
        default=False,
        help_text="If True, the field is included in API responses but excluded from write operations (POST/PUT/PATCH).",
    )
    write_only = serializers.BooleanField(
        default=False,
        help_text="If True, the field can be sent in write operations but will be omitted from API responses.",
    )
    required = serializers.BooleanField(
        default=True,
        help_text="Indicates whether the field must be present in the input data during validation.",
    )
    default = serializers.CharField(
        allow_null=True,
        required=False,
        help_text="The default value used for the field if no input value is supplied.",
    )
    allow_blank = serializers.BooleanField(
        default=False,
        help_text="If True, empty string values ('') are considered valid input. Applicable to string-based fields.",
    )
    allow_null = serializers.BooleanField(
        default=False,
        help_text="If True, None/null is accepted as a valid value for the field.",
    )
    style = serializers.JSONField(
        default=dict,
        help_text="A dictionary of styling hints used to control how the field renders in browsable APIs or HTML forms.",
    )
    label = serializers.CharField(
        allow_null=True,
        required=False,
        help_text="A short text string used as the UI label or display name for the field.",
    )
    help_text = serializers.CharField(
        allow_null=True,
        required=False,
        help_text="A descriptive text string used to document or explain the field's purpose in UI forms and API schemas.",
    )
    initial = serializers.CharField(
        default="",
        required=False,
        help_text="A value used to pre-populate HTML forms in the browsable API when creating a new instance.",
    )
    max_length = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text="The maximum number of characters allowed for a string field.",
    )
    min_length = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text="The minimum number of characters required for a string field.",
    )
    trim_whitespace = serializers.BooleanField(
        default=True,
        help_text="If True, leading and trailing whitespace will be automatically stripped from string inputs.",
    )
    min_value = serializers.FloatField(
        allow_null=True,
        required=False,
        help_text="The minimum permitted numeric value for numeric fields.",
    )
    max_value = serializers.FloatField(
        allow_null=True,
        required=False,
        help_text="The maximum permitted numeric value for numeric fields.",
    )
    format = serializers.CharField(
        allow_null=True,
        required=False,
        help_text="Controls the output string formatting style, primarily used for Date, Time, and Decimal fields.",
    )
    input_formats = serializers.ListField(
        child=serializers.CharField(allow_null=True, required=False),
        help_text="A list of string formats that are explicitly accepted during parsing and validation (e.g., date formats).",
    )
    choices = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="A list of valid values or choice tuples (value, display_name) that the field can accept.",
    )
    html_cutoff = serializers.IntegerField(
        help_text="The maximum number of choices that will be rendered in HTML select dropdowns to prevent performance degradation."
    )
    html_cutoff_text = serializers.CharField(
        help_text="The string message displayed in HTML forms when the total available choices exceed the html_cutoff threshold."
    )
    allow_empty_files = serializers.BooleanField(
        help_text="If True, allows FileField or ImageField uploads to contain empty, zero-length files."
    )
    use_url = serializers.BooleanField(
        help_text="If True, file-based fields will return the full URL to the file in responses instead of just the filename."
    )
    allow_empty = serializers.BooleanField(
        help_text="If True, allows collection-based fields (like ListField or ManyRelatedField) to pass validation with zero elements."
    )
    child = serializers.JSONField(
        help_text="The configuration metadata representing the underlying DRF field type used to validate each item within a collection."
    )


class FieldSerializer(serializers.Serializer):
    type = serializers.CharField(
        required=True,
        help_text="The class name of the REST framework field (e.g., 'CharField', 'IntegerField', 'BooleanField').",
    )
    name = serializers.CharField(
        required=True,
        help_text="The name identifying this field on the parent object.",
    )
    attrs = FieldAttributesSerializer(
        required=True,
        help_text="A structured object containing the REST framework field's attributes",
    )


class FieldsetSerializer(serializers.Serializer):
    title = serializers.CharField(help_text=_("Fieldset title"))
    fields = serializers.ListField(
        child=serializers.JSONField(),
        help_text=_("List of field names or nested lists of field names"),
    )


class PrepopulatedFieldsSerializer(serializers.Serializer):
    mapping = serializers.DictField(
        child=serializers.ListField(
            child=serializers.CharField(),
            help_text=_(
                "List of source field names whose values are concatenated to "
                "populate the target field."
            ),
        ),
        help_text=_(
            "Dictionary where each key is the name of a field that will be "
            "pre-populated, and the value is a list of source field names."
        ),
    )


class PermissionsSerializer(serializers.Serializer):
    has_add_permission = serializers.BooleanField(
        required=True,
        help_text="Whether the user has permission to add new instances of the model.",
    )
    has_change_permission = serializers.BooleanField(
        required=True,
        help_text="Whether the user has permission to change existing instances of the model.",
    )
    has_delete_permission = serializers.BooleanField(
        required=True,
        help_text="Whether the user has permission to delete instances of the model.",
    )
    has_view_permission = serializers.BooleanField(
        required=True,
        help_text="Whether the user has permission to view instances of the model.",
    )


class FormSerializer(serializers.Serializer):
    model = serializers.CharField(
        help_text="A string made up of the app_label and model._meta.verbose_name separated by a dot.",
        required=True,
    )
    readonly_fields = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="A list of field names that are read-only and cannot be edited.",
    )
    fields = FieldSerializer(
        many=True,
        required=True,
        help_text="An list of serializer field names and attributes",
    )
    fieldsets = serializers.ListField(
        child=FieldsetSerializer(),
        help_text=_(
            "Admin fieldsets configuration matching Django admin's fieldsets structure."),
        required=True,
    )
    prepopulated_fields = PrepopulatedFieldsSerializer(
        required=True,
        help_text=_("Auto-populate fields based on other fields."),
    )
    permissions = PermissionsSerializer(
        required=True,
        help_text=_("User permissions for the model."),
    )
    save_as = serializers.BooleanField(
        required=True, help_text="enable a “save as new” feature on admin change forms")
    save_as_continue = serializers.BooleanField(
        required=True, help_text="When True, the default redirect after saving the new object is to the change view for that object")
    save_on_top = serializers.BooleanField(
        required=True, help_text="Add save buttons across the top of your admin change forms")
    filter_horizontal = serializers.ListField(
        child=serializers.CharField(),
        required=True, help_text="Horizontal filter widgets to render for ModelForms with ManyToManyFields")
    filter_vertical = serializers.ListField(
        child=serializers.CharField(),
        required=True, help_text="Vertical filter widgets to render for ModelForms with ManyToManyFields")
    raw_id_fields = serializers.ListField(
        child=serializers.CharField(),
        required=True, help_text="Automatically turn any ForeignKey or ManyToManyField into a raw HTML input widget")
    radio_fields = serializers.DictField(
        child=serializers.CharField(),
        required=True, help_text="Fields to render as radio buttons")
    view_on_site = serializers.BooleanField(
        required=True, help_text="Whether to display a link to view the object on the site")
    autocomplete_fields = serializers.ListField(
        child=serializers.CharField(),
        required=True, help_text="Fields to use with autocomplete widgets")


class InlineSerializer(serializers.Serializer):
    model = serializers.CharField(
        help_text="A string made up of the app_label and model._meta.verbose_name separated by a dot.",
        required=True,
    )
    readonly_fields = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="A list of field names that are read-only and cannot be edited.",
    )
    fieldsets = serializers.ListField(
        child=FieldsetSerializer(),
        help_text=_(
            "Admin fieldsets configuration matching Django admin's fieldsets structure."),
        required=True,
    )
    prepopulated_fields = PrepopulatedFieldsSerializer(
        required=True,
        help_text=_("Auto-populate fields based on other fields."),
    )
    permissions = PermissionsSerializer(
        required=True,
        help_text=_("User permissions for the model."),
    )
    extra = serializers.IntegerField(
        required=True,
        help_text=_("Number of extra forms to display."),
    )
    min_num = serializers.IntegerField(
        required=True,
        help_text=_("Minimum number of forms to display."),
    )
    max_num = serializers.IntegerField(
        required=True,
        help_text=_("Maximum number of forms to display."),
    )
    verbose_name = serializers.CharField(
        required=True,
        help_text=_("Verbose name for the model."),
    )
    verbose_name_plural = serializers.CharField(
        required=True,
        help_text=_("Verbose name plural for the model."),
    )
    can_delete = serializers.BooleanField(
        required=True,
        help_text=_("Whether the model can be deleted."),
    )
    show_change_link = serializers.BooleanField(
        required=True,
        help_text=_("Whether to show a change link for the model."),
    )
    admin_style = serializers.CharField(
        required=True,
        help_text=_("Admin style for the model."),
    )
    formset = serializers.ListField(
        child=serializers.ListField(child=FieldSerializer()),
        required=True,
        help_text=_(
            "The formset configuration for the model a list of lists of field definitions."),
    )


class FormFieldsSerializer(serializers.Serializer):
    form = FormSerializer(required=True, help_text=_(
        "The form configuration for the model."))
    inlines = InlineSerializer(many=True, required=True, help_text=_(
        "The inlines configuration for the model."))


class URLsSerializer(serializers.Serializer):
    url = serializers.URLField(help_text=_("The URL of the endpoint."))


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
        help_text=_("Whether the user has permission to access the site.")
    )
    available_apps = AppSerializer(
        many=True, help_text=_("The list of applications available to the user.")
    )
    is_nav_siderbar_enabled = serializers.BooleanField(
        help_text=_("Whether the navigation sidebar is enabled.")
    )


class ActionChoiceSerializer(serializers.Serializer):
    action = serializers.CharField(
        help_text=_("The internal name of the action."))
    description = serializers.CharField(help_text=_(
        "The human-readable description of the action."))


class FilterChoiceSerializer(serializers.Serializer):
    selected = serializers.BooleanField(help_text=_(
        "Whether this filter choice is currently selected."))
    query_string = serializers.CharField(help_text=_(
        "The query string to apply this filter choice."))
    display = serializers.CharField(help_text=_(
        "The human-readable label for this filter choice."))


class FilterSerializer(serializers.Serializer):
    title = serializers.CharField(help_text=_("The title of the filter."))
    choices = FilterChoiceSerializer(many=True, help_text=_(
        "The list of available choices for this filter."))


class EditingFieldSerializer(serializers.Serializer):
    type = serializers.CharField(help_text=_("The field type for editing."))
    name = serializers.CharField(help_text=_("The name of the field."))
    attrs = serializers.DictField(help_text=_(
        "The attributes and configuration for the editing field."))


class ConfigSerializer(serializers.Serializer):
    actions_on_top = serializers.BooleanField(help_text=_(
        "Whether to display actions at the top of the list."))
    actions_on_bottom = serializers.BooleanField(help_text=_(
        "Whether to display actions at the bottom of the list."))
    actions_selection_counter = serializers.BooleanField(
        help_text=_("Whether to show a counter for selected items."))
    empty_value_display = serializers.CharField(
        help_text=_("The string to display for empty values."))
    list_display = serializers.ListField(child=serializers.CharField(
    ), help_text=_("The fields to display in the list."))
    list_display_links = serializers.ListField(child=serializers.CharField(
    ), help_text=_("The fields that should link to the change view."))
    list_editable = serializers.ListField(child=serializers.CharField(
    ), help_text=_("The fields that are editable directly in the list."))
    exclude = serializers.ListField(child=serializers.CharField(
    ), help_text=_("The fields to exclude from the list."))
    show_full_result_count = serializers.BooleanField(
        help_text=_("Whether to show the total count of results."))
    list_per_page = serializers.IntegerField(
        help_text=_("The number of items to show per page."))
    list_max_show_all = serializers.IntegerField(help_text=_(
        "The maximum number of items to show when 'Show all' is clicked."))
    date_hierarchy = serializers.CharField(help_text=_(
        "The field to use for date-based navigation."))
    search_help_text = serializers.CharField(allow_null=True, help_text=_(
        "The help text to display for the search box."))
    sortable_by = serializers.ListField(
        child=serializers.CharField(), allow_null=True, help_text=_("The fields that the user can sort by."))
    search_fields = serializers.ListField(child=serializers.CharField(
    ), help_text=_("The fields to include in the search."))
    preserve_filters = serializers.BooleanField(help_text=_(
        "Whether to preserve filters after saving an object."))
    full_count = serializers.IntegerField(help_text=_(
        "The total number of objects in the database."))
    result_count = serializers.IntegerField(help_text=_(
        "The number of objects matching the current filters."))
    action_choices = ActionChoiceSerializer(
        many=True, help_text=_("The list of available actions."))
    filters = FilterSerializer(many=True, help_text=_(
        "The list of available filters."))
    list_display_fields = serializers.ListField(child=serializers.CharField(
    ), help_text=_("The list of fields available for list display."))
    editing_fields = serializers.ListField(child=EditingFieldSerializer(
    ), help_text=_("Metadata for list-editable fields."))


class ColumnSerializer(serializers.Serializer):
    field = serializers.CharField(help_text=_(
        "The field name associated with this column."))
    headerName = serializers.CharField(help_text=_(
        "The human-readable header name for this column."))


class RowSerializer(serializers.Serializer):
    change_url = serializers.URLField(help_text=_(
        "The URL to the change view for this object."))
    id = serializers.IntegerField(
        help_text=_("The primary key of the object."))
    cells = serializers.DictField(
        child=serializers.CharField(),
        help_text=_("The data cells for this row, mapped by field name."))


class ChangelistResponseSerializer(serializers.Serializer):
    action_form = FormFieldsSerializer(
        help_text=_(
            "Configuration for the action form, including fields and inlines.")
    )
    config = ConfigSerializer(
        help_text=_("Configuration metadata for the changelist.")
    )
    columns = ColumnSerializer(
        many=True, help_text=_("A list of column definitions for the table.")
    )
    rows = RowSerializer(
        many=True, help_text=_("The actual data rows to be displayed.")
    )


class ResponseMessageSerializer(serializers.Serializer):
    detail = serializers.CharField(
        help_text=_("A detailed description of the response message.")
    )


class ErrorMessageSerializer(serializers.Serializer):
    detail = serializers.CharField(
        help_text=_("A detailed description of the error or response.")
    )
