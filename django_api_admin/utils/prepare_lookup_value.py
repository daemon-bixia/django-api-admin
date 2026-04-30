# -----------------------------------------------------------------------------
# The code in this file is from Django (https://www.djangoproject.com/)
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
# Licensed under the BSD 3-Clause License.
# -----------------------------------------------------------------------------

def prepare_lookup_value(key, value, separator=","):
    """
    Return a lookup value prepared to be used in queryset filtering.
    """
    if isinstance(value, list):
        return [prepare_lookup_value(key, v, separator=separator) for v in value]
    # if key ends with __in, split parameter into separate values
    if key.endswith("__in"):
        value = value.split(separator)
    # if key ends with __isnull, special case '' and the string literals 'false' and '0'
    elif key.endswith("__isnull"):
        value = value.lower() not in ("", "false", "0")
    return value
