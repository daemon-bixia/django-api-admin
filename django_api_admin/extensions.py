from drf_spectacular.extensions import OpenApiAuthenticationExtension, OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes


class XSessionTokenScheme(OpenApiAuthenticationExtension):
    target_class = "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication"
    name = "XSessionToken"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-Session-Token",
            "description": "Session token. Only needed when using django-allauth's `app` authentication."
        }


class MethodFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "django_api_admin.fields.MethodField"

    def map_serializer_field(self, auto_schema, direction):
        method = getattr(self.target, "method", None)
        if not method:
            return build_basic_type(OpenApiTypes.STR)

        return auto_schema._map_response_type_hint(method)
