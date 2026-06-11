from django.forms.models import _get_foreign_key

from rest_framework import serializers
from rest_framework.fields import _UnvalidatedField
from rest_framework.utils.field_mapping import get_field_kwargs

from django_api_admin.utils.get_field_attributes import get_field_attributes
from django_api_admin.constants import READ_ONLY_FIELDS


def get_form_fields_description(serializer, model_admin, change=False):
    """
    Given a serializer this function picks which fields should be
    used to create forms.
    """
    form_fields = list()

    # Loop all serializer fields
    for name, field in serializer.fields.items():
        # Don't create a form field for the pk field, read_only, hidden, hyper linking, or method fields
        if name == "pk" or field.read_only or type(field).__name__ in READ_ONLY_FIELDS:
            continue

        # If it is an inline model, and the field is the foreign key used to
        # create the relationship between the parent model, and the inline don't include it.
        if model_admin.is_inline:
            fk = _get_foreign_key(model_admin.parent_model, model_admin.model, fk_name=model_admin.fk_name)
            if name == fk.name:
                continue

        # If it's a `ModelField` then get the attributes of the `mapped_field` not the ModelField itself
        # Hint: `ModelField` is a dynamic field `ModelSerializer`s use to map a Django Model's Field
        # instance to the correct DRF Serializer class
        if isinstance(type(field), serializers.ModelField):
            field_kwargs = get_field_kwargs(field.model_field.verbose_name, field.model_field)
            field = serializers.ModelSerializer.serializer_field_mapping[field.model_field.__class__](**field_kwargs)

        form_field = get_field_attributes(name, field, serializer, model_admin, change)

        # Include child field for composite fields (i.e ListField, DictField, HStoreField)
        if type(field) in [serializers.ListField, serializers.DictField, serializers.HStoreField] and isinstance(
            type(form_field["attrs"]["child"]), _UnvalidatedField
        ):
            form_field["attrs"]["child"] = get_field_attributes(field.child.field_name, field.child, change, serializer)
        # If no child set child to null
        elif isinstance(type(form_field["attrs"].get("child", None)), _UnvalidatedField):
            form_field["attrs"]["child"] = None

        form_fields.append(form_field)

    return form_fields
