from django.utils.translation import override as translation_override


def construct_change_message(request, main_result, inline_results, add):
    """
    Construct a JSON structure describing changes from a changed object.
    Translations are deactivated so that strings are stored untranslated.
    Translation happens later on LogEntry access.
    """
    change_message = []

    if add:
        change_message.append({"added": {}})
    elif main_result[1]:
        with translation_override(None):
            changed_field_labels = _get_changed_field_labels_from_serializer(
                *main_result)
        change_message.append({"changed": {"fields": changed_field_labels}})

    if inline_results:
        with translation_override(None):
            for operations in inline_results.values():
                for serializer in operations["add"]:
                    change_message.append(
                        {
                            "added": {
                                "name": str(serializer.instance._meta.verbose_name),
                                "object": str(serializer.instance),
                            }
                        }
                    )
                for serializer, changed_data in operations["change"]:
                    change_message.append(
                        {
                            "changed": {
                                "name": str(serializer.instance._meta.verbose_name),
                                "object": str(serializer.instance),
                                "fields": _get_changed_field_labels_from_serializer(
                                    serializer, changed_data
                                ),
                            }
                        }
                    )
                for serializer in operations["delete"]:
                    change_message.append(
                        {
                            "deleted": {
                                "name": str(serializer.instance._meta.verbose_name),
                                "object": str(serializer.instance),
                            }
                        }
                    )

    return change_message


def _get_changed_field_labels_from_serializer(serializer, changed_data):
    changed_field_labels = []

    for field_name in changed_data:
        try:
            verbose_field_name = serializer.fields[field_name].label or field_name
        except KeyError:
            verbose_field_name = field_name
        changed_field_labels.append(str(verbose_field_name))

    return changed_field_labels
