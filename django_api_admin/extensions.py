from drf_spectacular.extensions import OpenApiAuthenticationExtension


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
