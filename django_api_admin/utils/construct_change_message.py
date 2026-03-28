from django.utils.translation import override as translation_override
from rest_framework import relations


def construct_change_message(request, add_serializer, valid_serializers, add):
    """
    Construct a JSON structure describing changes from a changed object.
    Translations are deactivated so that strings are stored untranslated.
    Translation happens later on LogEntry access.
    """
    change_message = []

    if add:
        change_message.append({"added": {}})
    elif changed_data := get_changed_data(request, add_serializer):
        with translation_override(None):
            changed_field_labels = _get_changed_field_labels_from_serializer(
                add_serializer, changed_data
            )
        change_message.append({"changed": {"fields": changed_field_labels}})

    if valid_serializers:
        with translation_override(None):
            for inline_serializers in valid_serializers.values():
                for add_serializer in inline_serializers["add"]:
                    change_message.append(
                        {
                            "added": {
                                "name": str(add_serializer.instance._meta.verbose_name),
                                "object": str(add_serializer.instance),
                            }
                        }
                    )
                for change_serializer in inline_serializers["change"]:
                    change_message.append(
                        {
                            "changed": {
                                "name": str(change_serializer.instance._meta.verbose_name),
                                "object": str(change_serializer.instance),
                                "fields": _get_changed_field_labels_from_serializer(
                                    change_serializer, get_changed_data(
                                        request, change_serializer)
                                ),
                            }
                        }
                    )
                for delete_serializer in inline_serializers["delete"]:
                    change_message.append(
                        {
                            "deleted": {
                                "name": str(delete_serializer.instance._meta.verbose_name),
                                "object": str(delete_serializer.instance),
                            }
                        }
                    )

    return change_message


def get_changed_data(request, serializer):
    changed_fields = []
    validated_data = serializer.validated_data
    instance = serializer.instance

    for field_name, field in serializer.fields.items():
        if field.read_only:
            continue

        # Case 1: The "Star" Field (Flattened Data)
        if field.source in ['*', '.']:
            raw_data = serializer.initial_data.get(field_name)
            if raw_data is None:
                continue

            unpacked_data = field.to_internal_value(raw_data)

            for model_attr, new_val in unpacked_data.items():
                old_val = getattr(instance, model_attr, None)
                if old_val != new_val:
                    if field_name not in changed_fields:
                        changed_fields.append(field_name)

        # Case 2: Standard Field Mapping
        if field_name in validated_data:
            model_attr = field.source or field_name
            new_value = validated_data[field_name]
            old_value = getattr(instance, model_attr, None)

            if does_not_equal(request, field, old_value, new_value):
                changed_fields.append(field_name)

    return changed_fields


def does_not_equal(request, field, old_value, new_value):
    many = False

    if isinstance(field, relations.ManyRelatedField):
        field = field.child_relation
        many = True

    if isinstance(field, relations.RelatedField):
        if many:
            old_pks = list(old_value.values_list('pk', flat=True))
            new_pks = [v.pk for v in new_value]
            return old_pks != new_pks
        return old_value.pk != new_value.pk

    return old_value != new_value


def _get_changed_field_labels_from_serializer(serializer, changed_data):
    changed_field_labels = []

    for field_name in changed_data:
        try:
            verbose_field_name = serializer.fields[field_name].label or field_name
        except KeyError:
            verbose_field_name = field_name
        changed_field_labels.append(str(verbose_field_name))

    return changed_field_labels
