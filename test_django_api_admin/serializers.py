from rest_framework import serializers
from test_django_api_admin.models import Author, Publisher
from test_django_api_admin.fields import LocationField


class AuthorSerializer(serializers.ModelSerializer):
    location = LocationField(source="*", required=False)
    publisher = serializers.HyperlinkedRelatedField(
        many=True, view_name="publisher-detail", queryset=Publisher.objects.all())

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "age",
            "is_vip",
            "user",
            "publisher",
            "gender",
            "date_joined",
            "title",
            "location"
        ]
        read_only_fields = ['date_joined']


class PublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        fields = "__all__"
