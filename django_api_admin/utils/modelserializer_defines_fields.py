def modelserializer_defines_fields(serialize_class):
    return hasattr(serialize_class, "Meta") and (
        serialize_class.Meta.fields is not None or serialize_class.Meta.exclude is not None
    )
