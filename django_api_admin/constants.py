CORE_FIELD_ATTRIBUTES = [
    "read_only",
    "write_only",
    "required",
    "default",
    "allow_null",
    "label",
    "help_text",
    "initial",
    "style",
]

STRING_FIELDS_ATTRIBUTES = ["max_length", "min_length", "allow_blank", "trim_whitespace"]

NUMERIC_FIELDS_ATTRIBUTES = ["max_value", "min_value"]

DATETIME_FIELDS_ATTRIBUTES = ["format", "input_formats"]

CHOICE_FIELDS_ATTRIBUTES = ["choices", "allow_blank", "html_cutoff", "html_cutoff_text"]

FILE_FIELDS_ATTRIBUTES = ["max_length", "allow_empty_file", "use_url"]

COMPOSITE_FIELDS_ATTRIBUTES = ["child", "allow_empty"]

RELATIONSHIP_FIELDS_ATTRIBUTES = [
    "choices",
    "many",
    "html_cutoff",
    "html_cutoff_text",
]

SERIALIZER_FIELD_ATTRIBUTES = {
    # Boolean fields attributes
    "BooleanField": [*CORE_FIELD_ATTRIBUTES],
    # String fields attributes
    "CharField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES],
    "EmailField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES],
    "RegexField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES, "regex"],
    "SlugField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES, "allow_unicode"],
    "URLField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES],
    "UUIDField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES, "uuid_format"],
    "IPAddressField": [*CORE_FIELD_ATTRIBUTES, *STRING_FIELDS_ATTRIBUTES, "protocol", "unpack_ipv4"],
    "FilePathField": [*CORE_FIELD_ATTRIBUTES, *CHOICE_FIELDS_ATTRIBUTES],
    # Numeric fields
    "IntegerField": [*CORE_FIELD_ATTRIBUTES, *NUMERIC_FIELDS_ATTRIBUTES],
    "FloatField": [*CORE_FIELD_ATTRIBUTES, *NUMERIC_FIELDS_ATTRIBUTES],
    "DecimalField": [
        *CORE_FIELD_ATTRIBUTES,
        *NUMERIC_FIELDS_ATTRIBUTES,
        "max_digits",
        "decimal_places",
        "coerce_to_string",
        "localize",
        "rounding",
        "normalize_output",
    ],
    # Date and time fields attributes
    "DateTimeField": [*CORE_FIELD_ATTRIBUTES, *DATETIME_FIELDS_ATTRIBUTES, "timezone"],
    "DateField": [*CORE_FIELD_ATTRIBUTES, *DATETIME_FIELDS_ATTRIBUTES],
    "TimeField": [*CORE_FIELD_ATTRIBUTES, *DATETIME_FIELDS_ATTRIBUTES],
    "DurationField": [*CORE_FIELD_ATTRIBUTES, *NUMERIC_FIELDS_ATTRIBUTES],
    # Choice fields attributes
    "ChoiceField": [*CORE_FIELD_ATTRIBUTES, *CHOICE_FIELDS_ATTRIBUTES],
    "MultipleChoiceField": [*CORE_FIELD_ATTRIBUTES, *CHOICE_FIELDS_ATTRIBUTES, "allow_empty"],
    # File fields attributes
    "FileField": [*CORE_FIELD_ATTRIBUTES, *FILE_FIELDS_ATTRIBUTES],
    "ImageField": [*CORE_FIELD_ATTRIBUTES, *FILE_FIELDS_ATTRIBUTES],
    # Composite fields
    "ListField": [*CORE_FIELD_ATTRIBUTES, *COMPOSITE_FIELDS_ATTRIBUTES, "min_length", "max_length"],
    "DictField": [*CORE_FIELD_ATTRIBUTES, *COMPOSITE_FIELDS_ATTRIBUTES],
    "HStoreField": [*CORE_FIELD_ATTRIBUTES, *COMPOSITE_FIELDS_ATTRIBUTES],
    "JSONField": [*CORE_FIELD_ATTRIBUTES, "binary"],
    # Miscellaneous fields
    "ReadOnlyField": [*CORE_FIELD_ATTRIBUTES],
    "HiddenField": [*CORE_FIELD_ATTRIBUTES],
    "ModelField": [*CORE_FIELD_ATTRIBUTES],
    "SerializerMethodField": [*CORE_FIELD_ATTRIBUTES],
    # Relationships fields
    "StringRelatedField": [*CORE_FIELD_ATTRIBUTES, *RELATIONSHIP_FIELDS_ATTRIBUTES],
    "ManyRelatedField": [*CORE_FIELD_ATTRIBUTES, *RELATIONSHIP_FIELDS_ATTRIBUTES],
    "PrimaryKeyRelatedField": [*CORE_FIELD_ATTRIBUTES, *RELATIONSHIP_FIELDS_ATTRIBUTES],
    "HyperlinkedRelatedField": [*CORE_FIELD_ATTRIBUTES, *RELATIONSHIP_FIELDS_ATTRIBUTES],
    "SlugRelatedField": [*CORE_FIELD_ATTRIBUTES, *RELATIONSHIP_FIELDS_ATTRIBUTES, "slug_field"],
    "HyperlinkedIdentityField": [*CORE_FIELD_ATTRIBUTES, *RELATIONSHIP_FIELDS_ATTRIBUTES],
}

READ_ONLY_FIELDS = ["HiddenField", "ReadOnlyField", "SerializerMethodField", "HyperlinkedIdentityField"]
