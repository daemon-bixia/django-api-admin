IS_POPUP_VAR = "_popup"
TO_FIELD_VAR = "_to_field"
LOOKUP_SEP = "__"
EMPTY_VALUE_STRING = "-"

HORIZONTAL, VERTICAL = 1, 2

# Changelist settings
ALL_VAR = "all"
ORDER_VAR = "o"
PAGE_VAR = "p"
SEARCH_VAR = "q"
ERROR_FLAG = "e"

# DRF field attributes
SHARED_FIELD_ATTRIBUTES = [
    "read_only", "write_only", "required", "default",
    "allow_blank", "allow_null", "style", "label",
    "help_text", "initial",
]

SHARED_STRING_FIELDS_ATTRIBUTES = [
    "max_length", "min_length", "trim_whitespace"]

SHARED_NUMERIC_FIELDS_ATTRIBUTES = ["max_value", "min_value"]

SHARED_DATETIME_FIELDS_ATTRIBUTES = ["format", "input_formats", ]

SHARED_CHOICE_FIELDS_ATTRIBUTES = [
    "choices", "allow_blank", "html_cutoff", "html_cutoff_text"]

SHARED_FILE_FIELDS_ATTRIBUTES = ["max_length", "allow_empty_file", "use_url"]

SHARED_COMPOSITE_FIELDS_ATTRIBUTES = ["child", "allow_empty"]

SHARED_RELATIONSHIP_FIELDS_ATTRIBUTES = [
    "choices", "many", "html_cutoff", "html_cutoff_text",
]

SERIALIZER_FIELD_ATTRIBUTES = {
    # boolean fields attributes
    "BooleanField": [*SHARED_FIELD_ATTRIBUTES],

    # String fields attributes
    "CharField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES],
    "EmailField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES],
    "RegexField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES, "regex"],
    "SlugField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES, "allow_unicode"],
    "URLField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES],
    "UUIDField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES, "format"],
    "IPAddressField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_STRING_FIELDS_ATTRIBUTES, "protocol", "unpack_ipv4"],
    "FilePathField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_CHOICE_FIELDS_ATTRIBUTES,
                      "path", "match", "recursive", "allow_files", "allow_folders"],

    # Numeric fields
    "IntegerField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_NUMERIC_FIELDS_ATTRIBUTES],
    "FloatField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_NUMERIC_FIELDS_ATTRIBUTES],
    "DecimalField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_NUMERIC_FIELDS_ATTRIBUTES, "max_digits", "decimal_places",
                     "coerce_to_string", "localize", "rounding"],

    # Date and time fields attributes
    "DateTimeField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_DATETIME_FIELDS_ATTRIBUTES],
    "DateField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_DATETIME_FIELDS_ATTRIBUTES],
    "TimeField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_DATETIME_FIELDS_ATTRIBUTES],
    "DurationField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_NUMERIC_FIELDS_ATTRIBUTES],

    # Choice fields attributes
    "ChoiceField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_CHOICE_FIELDS_ATTRIBUTES],
    "MultipleChoiceField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_CHOICE_FIELDS_ATTRIBUTES],

    # File fields attributes
    "FileField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_FILE_FIELDS_ATTRIBUTES],
    "ImageField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_FILE_FIELDS_ATTRIBUTES],

    # Composite fields
    "ListField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_COMPOSITE_FIELDS_ATTRIBUTES, "min_length", "max_length", ],
    "DictField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_COMPOSITE_FIELDS_ATTRIBUTES],
    "HStoreField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_COMPOSITE_FIELDS_ATTRIBUTES],
    "JSONField": [*SHARED_FIELD_ATTRIBUTES, "binary"],

    # Miscellaneous fields
    "ReadOnlyField": [*SHARED_FIELD_ATTRIBUTES],
    "HiddenField": [*SHARED_FIELD_ATTRIBUTES],
    "ModelField": [*SHARED_FIELD_ATTRIBUTES],
    "SerializerMethodField": [*SHARED_FIELD_ATTRIBUTES],

    # relationships fields
    "ManyRelatedField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_RELATIONSHIP_FIELDS_ATTRIBUTES],
    "PrimaryKeyRelatedField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_RELATIONSHIP_FIELDS_ATTRIBUTES],
    "HyperlinkedRelatedField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_RELATIONSHIP_FIELDS_ATTRIBUTES],
    "SlugRelatedField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_RELATIONSHIP_FIELDS_ATTRIBUTES],
    "HyperlinkedIdentityField": [*SHARED_FIELD_ATTRIBUTES, *SHARED_RELATIONSHIP_FIELDS_ATTRIBUTES],
}
