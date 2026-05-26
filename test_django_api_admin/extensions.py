from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class LocationFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "test_django_api_admin.fields.LocationField"

    def map_serializer_field(self, auto_schema, direction):
        return {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lng": {"type": "number"},
            },
            "required": ["lat", "lng"],
        }
