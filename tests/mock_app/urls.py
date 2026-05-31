from django.urls import path
from .admin import site

urlpatterns = [
    path("api_admin/", site.urls),
]
