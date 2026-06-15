from django.contrib import admin
from django.urls import path, include

from shop.admin import site

urlpatterns = [
    # Both the api admin and the default admin
    path("admin/", admin.site.urls),
    path("api_admin/", site.urls),
    # The admin panel uses the same authentication backend as the application
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/", include("allauth.urls")),
]
