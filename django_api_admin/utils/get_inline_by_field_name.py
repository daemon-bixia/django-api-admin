def get_inline_by_field_name(request, model_admin, inline_name):
    """
    Extract the InlineModelAdmin from the ModelAdmin using the inline_name value
    """
    inline_admin = None
    for inline_instance in model_admin.get_inline_instances(request):
        if inline_instance.model._meta.verbose_name_plural == inline_name:
            inline_admin = inline_instance
    return inline_admin
