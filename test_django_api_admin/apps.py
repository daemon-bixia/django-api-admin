from django.apps import AppConfig


class TestDjangoApiAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "test_django_api_admin"

    def ready(self):
        try:
            import test_django_api_admin.extensions  # noqa: F401
        except ImportError:
            pass
