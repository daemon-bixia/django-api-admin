from django.db import router
from django.utils.translation import gettext as _
from django.forms.models import _get_foreign_key
from django.contrib.admin.utils import NestedObjects
from django.utils.text import get_text_list

from rest_framework.exceptions import NotFound

from django_api_admin.utils.get_related_name import get_related_name
from django_api_admin.utils.get_changed_data import get_changed_data
from django_api_admin.utils.format_error import format_error


class InlineBulkOperation:
    errors = {}
    result = {}

    def __init__(self, request, model_admin, obj, data):
        self.request = request
        self.model_admin = model_admin
        self.obj = obj
        self.data = data

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
        model_ids = ["%s.%s" % (i.model._meta.app_label, i.model._meta.model_name) for i in inlines]

        # Make sure all the keys of `data` are valid `inline_names`.
        for key in self.data.keys():
            if key not in model_ids:
                self.errors[key] = {
                    "non_form_errors": [
                        {"message": _("There is no inline admin with this name in model admin"), "param": "non_form_errors"}
                    ]
                }
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
                raise NotFound(
                    {"detail": _("Inline '%s' is not registered in '%s'" % (key, self.model_admin.__class__.__name__))}
                )

            serializer_class = inline.get_serializer_class(self.request)
            # Get the fk used to create the inline relationship
            fk = _get_foreign_key(inline.parent_model, inline.model, fk_name=inline.fk_name)
            related_name = fk.remote_field.accessor_name
            reverse_field = getattr(self.obj, related_name)
            related_instances_count = reverse_field.count()

            self.result[key] = {"add": [], "change": [], "delete": []}
            add_errors = {}
            change_errors = {}
            delete_errors = {}

            if "add" in value:
                for idx, data in enumerate(value["add"]):
                    # Validate the number of related instances does not exceed the
                    # `max_num` set at the inline model
                    if inline.max_num is not None and related_instances_count >= inline.max_num:
                        add_errors[idx] = [
                            {
                                "message": "Cannot exceed the `max_num` of `%s` allowed"
                                % (inline.model._meta.verbose_name_plural),
                                "param": "non_form_errors",
                            }
                        ]

                    # Add the object pk to the fk field to create the relationship
                    data[fk.name] = self.obj.pk
                    serializer_params = self.model_admin.get_inline_serializer_kwargs(self.request, "add", inline, data=data)
                    serializer = serializer_class(**serializer_params)

                    # Validate the add data using the inline serializer
                    if serializer.is_valid():
                        self.result[key]["add"].append(serializer)
                        related_instances_count += 1
                    else:
                        if idx in add_errors:
                            add_errors[idx] = [*add_errors[idx], *format_error(serializer.errors)]
                        else:
                            add_errors[idx] = format_error(serializer.errors)

            if "change" in value:
                fk_field = getattr(self.obj, get_related_name(fk), None)
                primary_keys = [data.get("pk") for data in value["change"]]
                instances = fk_field.filter(pk__in=primary_keys)

                for idx, data in enumerate(value["change"]):
                    # Add the object pk to the fk field to create the relationship
                    data[fk.name] = self.obj.pk
                    # Find the item to be updated in the queryset
                    instance = next((i for i in instances if i.pk == data.get("pk")), None)

                    # Validate that all primary_keys are valid instances
                    if not instance:
                        params = {
                            "parent_model": self.model_admin.model._meta.verbose_name,
                            "idx": idx,
                            "inline_model": inline.model._meta.verbose_name,
                        }
                        change_errors[idx] = [
                            {
                                "message": _(
                                    "Couldn't find %(parent_model)s associated with the data at index "
                                    "%(idx)s, check that the 'pk' value "
                                    "represents a valid %(inline_model)s in the database" % params
                                ),
                                "param": "pk",
                            }
                        ]

                    # Validate the change data using the inline serializer
                    if idx not in change_errors:
                        serializer_params = self.model_admin.get_inline_serializer_kwargs(
                            self.request, "change", inline, instance=instance, data=data
                        )
                        serializer = serializer_class(**serializer_params)

                        if serializer.is_valid():
                            changed_data = get_changed_data(serializer)
                            self.result[key]["change"].append((serializer, changed_data))
                        else:
                            change_errors[idx] = format_error(serializer.errors)

            if "delete" in value:
                primary_keys = [pk for pk in value["delete"]]
                instances = list(inline.model.objects.filter(pk__in=primary_keys))

                # Validate the primary keys, and instances
                for idx, pk in enumerate(value["delete"]):
                    instance = next((i for i in instances if i.pk == pk), None)

                    # Validate the number of instances is not less than the `min_num`
                    # set at the inline model
                    if inline.min_num is not None and related_instances_count <= inline.min_num:
                        delete_errors[idx] = [
                            {
                                "message": "Cannot fall short of the `min_num` of `%s` allowed"
                                % (inline.model._meta.verbose_name_plural),
                                "param": "non_field_errors",
                            }
                        ]

                    # Validate that all primary_keys are valid instances
                    if not instance:
                        params = {
                            "parent_model": self.model_admin.model._meta.verbose_name,
                            "idx": idx,
                            "inline_model": inline.model._meta.verbose_name,
                        }
                        msg = _(
                            (
                                "Couldn't find %(parent_model)s associated with the data "
                                "at index %(idx)s, check that the 'pk' value "
                                "represents a valid %(inline_model)s in the database"
                            )
                            % params
                        )
                        error = {"message": [msg], "param": "pk"}
                        if idx not in delete_errors:
                            delete_errors[idx] = [error]
                        else:
                            delete_errors[idx].append(error)
                        continue

                    # Ensure no related "protected" records are going to be deleted
                    using = router.db_for_write(inline.model)
                    collector = NestedObjects(using=using)
                    collector.collect([instance])
                    if collector.protected:
                        objs = []
                        for p in collector.protected:
                            objs.append(_("%(class_name)s %(instance)s") % {"class_name": p._meta.verbose_name, "instance": p})
                        params = {
                            "class_name": inline.model._meta.verbose_name,
                            "instance": instance,
                            "related_objects": get_text_list(objs, _("and")),
                        }
                        msg = _(
                            "Deleting %(class_name)s %(instance)s would require "
                            "deleting the following protected related objects: "
                            "%(related_objects)s" % params
                        )
                        if idx in delete_errors:
                            delete_errors[idx] = [*delete_errors[idx], msg]
                        else:
                            delete_errors[idx] = [msg]

                    # Create a serializer for the instance to be deleted
                    if idx not in delete_errors:
                        serializer_params = self.model_admin.get_inline_serializer_kwargs(
                            self.request, "delete", inline, instance=instance
                        )
                        serializer = serializer_class(**serializer_params)
                        self.result[key]["delete"].append(serializer)
                        related_instances_count -= 1

            # If there are errors include them under the `model_id`
            if add_errors or change_errors or delete_errors:
                self.errors[key] = {}
                if add_errors:
                    self.errors[key]["add"] = add_errors
                if change_errors:
                    self.errors[key]["change"] = change_errors
                if delete_errors:
                    self.errors[key]["delete"] = delete_errors
                valid = False

        return valid

    def get_inline_by_model_id(self, model_id):
        """
        Get the inline instance that match the given model_id
        (i.e 'app_label.model_name') in the `self.model_admin.inlines`
        """
        inlines = self.model_admin.get_inline_instances(self.request)
        for inline in inlines:
            if model_id == "%s.%s" % (inline.model._meta.app_label, inline.model._meta.model_name):
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
                    data[inline_name][operation_name].append(serializer.data)

        return data


class ChangelistBulkOperation:
    errors = {}
    result = {}

    def __init__(self, request, model_admin, instances, data, serializer_class):
        self.request = request
        self.model_admin = model_admin
        self.instances = instances
        self.data = data
        self.serializer_class = serializer_class

    def is_valid(self):
        """
        Ensure all data is validated by the serializer correctly
        """

        if not self.data:
            self.errors["non_field_errors"] = ["Change data cannot be empty"]
            return False

        for idx, data in enumerate(self.data):
            pk = data["pk"]
            # Get the object we're editing
            instance = next((i for i in self.instances if i.pk == pk), None)
            if not instance:
                verbose_name = self.model_admin.model._meta.verbose_name
                self.errors[idx] = [
                    {
                        "message": _(
                            "Couldn't find %s associated with the data at row %s is not found,"
                            " check that the 'pk' value represents a valid %s in the database"
                            % (verbose_name, pk, verbose_name)
                        ),
                        "param": "pk",
                    }
                ]
                continue

            # Validate the object using the `serializer_class`
            serializer = self.serializer_class(instance, data=data)
            if serializer.is_valid():
                changed_data = get_changed_data(serializer)
                self.result[idx] = (serializer, changed_data)
            else:
                self.errors[idx] = format_error(serializer.errors)

        return not bool(self.errors)

    @property
    def validated_data(self):
        data = dict()

        for idx, (serializer, changed_data) in self.result.items():
            data[idx] = serializer.data

        return data
