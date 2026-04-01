from django.utils.translation import gettext_lazy as _
from django.forms.models import _get_foreign_key

from rest_framework.exceptions import NotFound

from django_api_admin.utils.get_related_name import get_related_name
from django_api_admin.utils.get_changed_data import get_changed_data


class BulkOperation:
    errors = {}
    result = {}

    def __init__(self, request, model_admin, obj, data):
        self.request = request
        self.model_admin = model_admin
        self.data = data
        self.obj = obj

    def is_valid(self):
        if not self.keys_are_valid_inline_names():
            return False

        if not self.bulk_data_is_valid():
            return False

        return True

    def keys_are_valid_inline_names(self):
        """
        Validate that all keys in `self.data` are names of inlines associated with `self.model_admin`
        """
        valid = True

        # Generate a list of the inline model admin names associated with the model_admin.
        inlines = self.model_admin.get_inline_instances(self.request)
        model_ids = [
            "%s/%s" % (i.model._meta.app_label,
                       i.model._meta.model_name)
            for i in inlines
        ]

        # Make sure all the keys of `data` are valid `inline_names`.
        for key in self.data.keys():
            if key not in model_ids:
                self.errors[key] = {'non_field_errors': [
                    _("There is no inline admin with this name in model admin")
                ]}
                valid = False

        return valid

    def bulk_data_is_valid(self):
        """
        Instantiate a serializer for every set of data in every operation in `self.data`
        and call the `serializer.is_valid` method
        """
        valid = True

        for key, value in self.data.items():
            inline = self.get_inline_by_model_id(key)
            # Raise an error if an inline is not found
            if not inline:
                raise NotFound({"detail": _("Inline '%s' is not registered in '%s'" % (
                    key, self.model_admin.__class__.__name__))})

            serializer_class = inline.get_serializer_class(self.request)
            # Get the fk used to create the inline relationship
            fk = _get_foreign_key(inline.parent_model,
                                  inline.model, fk_name=inline.fk_name)

            self.result[key] = {
                "add": [], "change": [], "delete": []}
            add_errors = {}
            change_errors = {}
            delete_errors = {}

            if "add" in value:
                for row_id, data in value["add"].items():
                    # Add the object pk to the fk field to create the relationship
                    data[fk.name] = self.obj.pk
                    serializer = serializer_class(data=data)

                    if serializer.is_valid():
                        self.result[key]["add"].append(
                            serializer)
                    else:
                        add_errors[row_id] = serializer.errors

            if "change" in value:
                fk_field = getattr(self.obj, get_related_name(fk), None)
                primary_keys = [data.get("pk")
                                for data in value["change"].values()]
                instances = fk_field.filter(pk__in=primary_keys)

                for row_id, data in value["change"].items():
                    # Add the object pk to the fk field to create the relationship
                    data[fk.name] = self.obj.pk

                    # Find the item to be updated in the queryset
                    instance = next(
                        (i for i in instances if i.pk == data.get("pk")), None)
                    if not instance:
                        change_errors[row_id] = {
                            "pk": [_(
                                "Couldn't find %s associated with the data at row %s \
                                 is not found, check that the 'pk' value represents a  \
                                 valid %s in the database" % (self.model_admin.model._meta.verbose_name,
                                                              row_id, self.model_admin.model._meta.verbose_name))]
                        }
                        continue

                    serializer = serializer_class(
                        instance, data=data, partial=True)

                    if serializer.is_valid():
                        changed_data = get_changed_data(serializer)
                        self.result[key]["change"].append(
                            (serializer, changed_data))
                    else:
                        change_errors[row_id] = serializer.errors

            if "delete" in value:
                primary_keys = [pk for pk in value["delete"].values()]
                instances = list(
                    inline.model.objects.filter(pk__in=primary_keys))

                # Validate that all primary_keys are valid instances
                for row_id, pk in value["delete"].items():
                    idx, instance = next(
                        ((idx, i) for idx, i in enumerate(instances) if i.pk == pk), None)
                    if not instance:
                        delete_errors[row_id] = {
                            "pk": [_(
                                "Couldn't find %s associated with the data at row %s \
                                 is not found, check that the 'pk' value represents a  \
                                 valid %s in the database" % (self.model_admin.model.verbose_name,
                                                              row_id, self.model_admin.model.verbose_name))]
                        }
                        instances.pop(idx)

                for instance in instances:
                    serializer = serializer_class(instance)
                    self.result[key]["delete"].append(
                        serializer)

            # If there are errors include them under the `model_id`
            if add_errors or change_errors or delete_errors:
                self.errors[key] = {
                    **add_errors,
                    **change_errors,
                    **delete_errors
                }
                valid = False

        return valid

    def get_inline_by_model_id(self, model_id):
        """
        Get the inline instance that match the given model_id 
        (i.e 'app_label/model_name') in the `self.model_admin.inlines`
        """
        inlines = self.model_admin.get_inline_instances(self.request)
        for inline in inlines:
            if model_id == "%s/%s" % (inline.model._meta.app_label,
                                      inline.model._meta.model_name):
                return inline

    @property
    def validated_data(self):
        data = dict()

        for inline_name, operations in self.result.items():
            data[inline_name] = {}
            for operation_name, serializers in operations.items():
                data[inline_name][operation_name] = []
                for serializer in serializers:
                    if operation_name == "change":
                        serializer = serializer[0]
                    data[inline_name][operation_name].append(
                        serializer.data)

        return data

    def save(self):
        """
        Save the valid serializers, and delete the instances.
        """
        for model_operations in self.result.values():
            for operation, serializers in model_operations.items():
                for serializer in serializers:
                    if operation == "add":
                        serializer.save()
                    elif operation == "change":
                        serializer[0].save()
                    elif operation == "delete":
                        serializer.instance.delete()
