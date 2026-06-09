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
