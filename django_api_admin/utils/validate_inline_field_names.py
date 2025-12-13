from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


def validate_inline_field_names(request, inlines,  model_admin):
    """
    Validates a list of field names to make sure every name is a valid inline in the model_admin.
    """
    # Generate a list containing names of the fields to add and update model admins.
    inline_admin_field_names = []
    for inline_admin in model_admin.get_inline_instances(request):
        inline_admin_field_names.append(
            inline_admin.model._meta.verbose_name_plural)

    # Make sure the user used the correct inline names.
    name_errors = {}
    for inline_name in inlines.keys():
        if inline_name not in inline_admin_field_names:
            name_errors[inline_name] = [
                _("there is no inline admin with this name in model admin")]

    # Raise inline doesn't exist error
    if len(name_errors):
        raise serializers.ValidationError({"inline_errors": name_errors})
