# -----------------------------------------------------------------------------
# The code in this file is from Django (https://www.djangoproject.com/)
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
# Licensed under the BSD 3-Clause License.
# -----------------------------------------------------------------------------

from django_api_admin.utils import get_model_from_relation
from django_api_admin.exceptions import NotRelationField
from django_api_admin.constants.vars import LOOKUP_SEP


def reverse_field_path(model, path):
    """Create a reversed field path.

    E.g. Given (Order, "user__groups"),
    return (Group, "user__order").

    Final field must be a related model, not a data field.
    """
    reversed_path = []
    parent = model
    pieces = path.split(LOOKUP_SEP)
    for piece in pieces:
        field = parent._meta.get_field(piece)
        # skip trailing data field if extant:
        if len(reversed_path) == len(pieces) - 1:  # final iteration
            try:
                get_model_from_relation(field)
            except NotRelationField:
                break

        # Field should point to another model
        if field.is_relation and not (field.auto_created and not field.concrete):
            related_name = field.related_query_name()
            parent = field.remote_field.model
        else:
            related_name = field.field.name
            parent = field.related_model
        reversed_path.insert(0, related_name)
    return (parent, LOOKUP_SEP.join(reversed_path))
