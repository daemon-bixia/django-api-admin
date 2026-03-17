from django.utils.translation import gettext_lazy as _
from django.forms.models import _get_foreign_key
from rest_framework.exceptions import NotFound


class BulkOperations:
    valid_serializers = {}
    errors = {}

    added = []
    changed = []
    deleted = []

    change_message = None

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

            serializer_class = inline.get_serializer_class()
            # Get the fk used to create the inline relationship
            fk = _get_foreign_key(inline.parent_model,
                                  inline.model, fk_name=inline.fk_name)

            self.valid_serializers[key] = {
                "add": [], "change": [], "delete": []}

            if hasattr(value, "add"):
                add_errors = {}

                for row_id, data in getattr(value, "add", {}).items():
                    # Add the object pk to the fk field to create the relationship
                    data[fk.name] = self.obj.pk
                    serializer = serializer_class(data=data)

                    if serializer.is_valid():
                        self.valid_serializers["add"].append(serializer)
                    else:
                        add_errors[row_id] = ({
                            [row_id]: serializer.errors,
                        })

            if hasattr(value, "change"):
                change_errors = {}
                fk_field = self.get_related_name(fk)
                primary_keys = [data['pk'] for data in value["change"]]
                instances = fk_field.filter(pk__in=primary_keys)

                for row_id, data in getattr(value, "change", {}).items():
                    # Add the object pk to the fk field to create the relationship
                    data[fk.name] = self.obj.pk

                    # Find the item to be updated in the queryset
                    instance = next(i for i in instances if i.pk == data['pk'])
                    if not instance:
                        change_errors[row_id] = {
                            [row_id]: [{
                                "param": data["pk"],
                                "message": _("Item with pk %s is not found" % data["pk"])
                            }]
                        }
                        continue

                    serializer = serializer_class(
                        instance, data=data, partial=True)

                    if serializer.is_valid():
                        self.valid_serializers["change"].append(serializer)
                    else:
                        change_errors[row_id] = serializer.errors

            if hasattr(value, "delete"):
                delete_errors = {}
                primary_keys = [pk for pk in value["delete"]]
                instances = inline.model.objects.filter(pk__in=primary_keys)

                # Validate that all primary_keys are valid instances
                for row_id, pk in getattr(value, "delete", {}):
                    instance, idx = next(
                        (i, idx) for i, idx in enumerate(instances) if i.pk == pk)
                    if not instance:
                        delete_errors[row_id] = [
                            {"param": pk, "message": _(
                                "Item with pk %s is not found" % data["pk"])}
                        ]
                        instances.pop(idx)

                for instance in instances:
                    serializer = serializer_class(instance)
                    self.valid_serializers["delete"].append(serializer)

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

    def get_related_name(self, fk):
        """
        Returns the name used to link the foreign key relationship.
        """
        if fk._related_name:
            return fk._related_name
        return fk.model._meta.model_name + "_set"

    def save(self):
        """
        Save the valid serializers, and delete the instances.
        """
        for model_operations in self.valid_serializers:
            for operation, serializers in model_operations.items():
                for serializer in serializers:
                    if operation == "add":
                        serializer.save()
                        self.added.append(serializer.data)
                    elif operation == "change":
                        serializer.save()
                        self.changed.append(serializer.data)
                    elif operation == "delete":
                        serializer.instance.delete()
                        self.deleted.append(serializer.data)
