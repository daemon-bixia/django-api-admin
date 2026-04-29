from functools import reduce
from operator import or_

from django.db import models


def build_q_object_from_lookup_parameters(parameters):
    q_object = models.Q()
    for param, param_item_list in parameters.items():
        q_object &= reduce(or_, (models.Q((param, item))
                           for item in param_item_list))
    return q_object
