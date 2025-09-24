from django.conf import settings

DEFAULTS = {
    "MFA_SAFE_PERIOD": 3 * 24 * 60 * 60 * 1000,  # 3 days
}


class AppSettings:

    def __getattr__(self, name):
        if name in DEFAULTS:
            return getattr(settings, name, DEFAULTS)


app_settings = AppSettings()
