# -----------------------------------------------------------------------------
# The code in this file is from Django (https://www.djangoproject.com/)
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
# Licensed under the BSD 3-Clause License.
# -----------------------------------------------------------------------------

from django_api_admin.exceptions import NotRelationField


def get_model_from_relation(field):
    if hasattr(field, "path_infos"):
        return field.path_infos[-1].to_opts.model
    else:
        raise NotRelationField
