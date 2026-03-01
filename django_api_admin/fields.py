import re
import copy
from rest_framework.fields import Field

REGEX_TYPE = type(re.compile(''))


class MethodField(Field):
    def __init__(self, method, **kwargs):
        self.method = method
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return self.method(value, self.context)

    def __deepcopy__(self, memo):
        args = [
            copy.deepcopy(item, memo) if not (isinstance(
                item, REGEX_TYPE) or item is self.method) else item
            for item in self._args
        ]
        kwargs = {
            key: (copy.deepcopy(value, memo) if (
                key not in ('validators', 'regex') and value is not self.method) else value)
            for key, value in self._kwargs.items()
        }
        return self.__class__(*args, **kwargs)
