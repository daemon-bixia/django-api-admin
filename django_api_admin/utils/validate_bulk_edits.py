from django.forms.models import _get_foreign_key

from django_api_admin.utils.validate_inline_field_names import validate_inline_field_names
from django_api_admin.utils.get_inline_by_field_name import get_inline_by_field_name
from django_api_admin.utils.get_related_name import get_related_name

from rest_framework import serializers


def validate_bulk_edits(request, model_admin, obj, operation="create_inlines"):
    """
    Validates the data used to create inline instances by finding each InlineAdmin's serializer class, 
    instantiating a serializer for every inline instance, or data, and calling the is_valid method of every serializer.
    We raise an exception if a single serializer is not valid.
    """
    # Validate the names of the fields
    # Hint: to make sure every name is a valid inline in the model_admin raises an exception if one not
    validate_inline_field_names(
        request, request.data.get(operation), model_admin)

    # Validate the inline data
    valid_serializers = []
    serializer_errors = []
    for inline_name, inline_data in request.data.get(operation).items():
        # Extract the InlineModelAdmin from the ModelAdmin using the inline_name
        inline_admin = get_inline_by_field_name(
            request, model_admin, inline_name)
        # Get the fk used to create the inline relationship
        fk = _get_foreign_key(inline_admin.parent_model,
                              inline_admin.model, fk_name=inline_admin.fk_name)
        # Get the serializer class
        serializer_class = inline_admin.get_serializer_class()

        # For the delete_inlines operation make sure all provided primary keys are related to the model...
        # ...and return a list of the deleted instances and their serialized data
        if operation == 'delete_inlines':
            serialized_instances = []
            # Get the list of all primary keys included in the datasets
            primary_keys = [
                inline_dataset['pk'] for inline_dataset in inline_data]
            # Get the instances to be deleted
            instances = inline_admin.model.objects.filter(
                pk__in=primary_keys)
            # If no instances are matched then raise an exception
            if instances.count() == 0:
                raise serializers.ValidationError(
                    {"error": "you did't include any inline that is related to this model"})
            # Make sure all instances are related to the model_admin model
            if instances.count() != len(primary_keys):
                raise serializers.ValidationError(
                    {"error": "you can't delete an inline that is not related to this model"})

            # Serialize the instance and add to the the array
            serializer_class = inline_admin.get_serializer_class()
            for instance in instances:
                serializer = serializer_class(instance)
                serialized_instances.append(serializer.data)

            return instances, serialized_instances

        # For the update_inlines operation we make sure all provided instances are related to the model...
        # ...and save them in the instances list for validation below
        instances = []
        if operation == "update_inlines":
            fk_field = getattr(obj, get_related_name(fk), None)
            primary_keys = [data['pk'] for data in inline_data]
            instances = fk_field.filter(pk__in=primary_keys)

            # If no instances are matched then raise an error
            if instances.count() == 0:
                raise serializers.ValidationError(
                    {"error": "you did't include any inline that is related to this model"})
            # Make sure all instances are related to the model_admin model
            if instances.count() != len(primary_keys):
                raise serializers.ValidationError(
                    {"error": "you can't update an inline that is not related to this model"})

        # Loop all data in the inline_data, and validate it using inline_serializer_class
        for idx, data in enumerate(inline_data):
            # Add the object pk to the fk field to create the relationship
            # Hint: this requires the object to be created
            data[fk.name] = obj.pk

            # Create the serializer instance
            inline_serializer = None
            if operation == "update_inlines":
                # For the update_inlines we create a serializer using the instance
                # Hint: we process each operation separately so instances[idx] will correct instance
                instance = instances[idx]
                inline_serializer = serializer_class(
                    instance, data=data, partial=True)
            else:
                # In the case of add view just create a serializer with the data
                inline_serializer = serializer_class(data=data)

            # Call the is_valid method
            if inline_serializer.is_valid():
                valid_serializers.append(inline_serializer)
            else:
                serializer_errors.append({
                    'errors': inline_serializer.errors,
                    'identifier': instances[idx].pk if operation == "update_inlines" else idx
                })

    # Respond with 400 in case of invalid data.
    if len(serializer_errors):
        raise serializers.ValidationError({"inline_errors": serializer_errors})

    return valid_serializers
