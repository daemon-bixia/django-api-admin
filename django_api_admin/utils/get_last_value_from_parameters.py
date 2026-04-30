def get_last_value_from_parameters(parameters, key):
    value = parameters.get(key)
    return value[-1] if isinstance(value, list) else value
