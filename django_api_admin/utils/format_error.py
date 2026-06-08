def format_error(errors):
    formatted_errors = []

    if isinstance(errors, list):
        for error in errors:
            for key, value in error.items():
                formatted_errors.append(
                    {
                        "message": " | ".join(value),
                        "param": key,
                    }
                )
    elif isinstance(errors, dict):
        for key, value in errors.items():
            formatted_errors.append(
                {
                    "message": " | ".join(value),
                    "param": key,
                }
            )

    return formatted_errors


def flatten_errors(idx, errors):
    flattened_errors = {}

    if isinstance(errors, dict):
        for key, value in errors.items():
            flattened_errors[f"{key}.{idx}"] = value

    elif isinstance(errors, list):
        for error in errors:
            for key, value in error.items():
                flattened_errors[f"{key}.{idx}"] = value

    return flattened_errors
