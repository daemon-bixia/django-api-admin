def get_form_config(model_admin):
    """
    Get model admin form attributes.
    """
    config = {}
    for option_name in model_admin.form_options:
        config[option_name] = getattr(model_admin, option_name, None)
    return config
