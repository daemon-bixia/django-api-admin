from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from rest_framework.serializers import ModelSerializer


def modelserializer_factory(
    model=None,
    serializer_class=ModelSerializer,
    fields=None,
    exclude=None,
    serializerfield_callback=None,
    read_only_fields=None,
    readonly_fields=None,
    depth=None,
    extra_kwargs=None,
    validators=None,
    list_serializer_class=None,
    class_name=None,
):
    """
    Return a ModelSerializer containing serializer fields for the given model. You can
    optionally pass a `serializer_class` argument to use as a starting point for
    constructing the ModelSerializer.
    """
    # Build up a list of attributes that the Meta object will have.
    attrs = {"model": model}
    if fields is not None:
        attrs["fields"] = fields
    if exclude is not None:
        attrs["exclude"] = exclude
    if read_only_fields is not None:
        attrs["read_only_fields"] = read_only_fields
    if readonly_fields is not None:
        attrs["read_only_fields"] = readonly_fields
    if depth is not None:
        attrs["depth"] = depth
    if extra_kwargs is not None:
        attrs["extra_kwargs"] = extra_kwargs
    if validators is not None:
        attrs["validators"] = validators
    if list_serializer_class is not None:
        attrs["list_serializer_class"] = list_serializer_class

    # If the parent model serializer defines a meta class we need to inherit from
    # that meta class
    bases = (serializer_class.Meta,) if hasattr(
        serializer_class, "Meta") else ()
    Meta = type("Meta", bases, attrs)

    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Overrides the default build_fields of the `ModelSerializer` class
        by calling the serializerfield_callback method to override the fields.
        """
        cls, kwargs = serializer_class.build_field(
            self, field_name, info, model_class, nested_depth)

        if field_name in info.fields_and_pk:
            db_field = info.fields_and_pk[field_name]
        elif field_name in info.relations:
            relation_info = info.relations[field_name]
            db_field = relation_info.model_field

        if db_field:
            serializerfield_kwargs = serializerfield_callback(
                db_field, **kwargs)

            # Remove the field
            if serializerfield_kwargs is None:
                return (lambda **kwargs: None, dict())

            return (cls, serializerfield_kwargs)

        return (cls, kwargs)

    # Class attributes for the new form class.
    serializer_class_attrs = {"Meta": Meta,
                              "build_field": cached_property(build_field)}

    # Give this new serializer class a reasonable name.
    serializer_class_name = class_name or model.__name__ + "Serializer"

    if getattr(Meta, "fields", None) is None and getattr(Meta, "exclude", None) is None:
        raise ImproperlyConfigured(
            "Calling modelserializer_factory without defining 'fields' or "
            "'exclude' explicitly is prohibited."
        )

    # Dynamically construct a model serializer
    return type(serializer_class)(
        serializer_class_name, (serializer_class,), serializer_class_attrs)
