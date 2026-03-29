from rest_framework import relations


def get_changed_data(serializer):
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

            if does_not_equal(field, old_value, new_value):
                changed_fields.append(field_name)

    return changed_fields


def does_not_equal(field, old_value, new_value):
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
