from django.contrib import admin
from django.urls import path, include

from test_django_api_admin import views
from test_django_api_admin.admin import site

urlpatterns = [
    # Both the api admin and the default admin
    path("admin/", admin.site.urls),
    path("api_admin/", site.urls),
    path("api/author/<int:pk>/",
         views.AuthorDetailView.as_view(), name="author-detail"),
    path("api/publisher/<int:pk>/",
         views.PublisherDetailView.as_view(), name="publisher-detail"),
    # The admin panel uses the same authentication backend as the application
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/", include("allauth.urls")),
    # Test your form fields.
    # path('api_admin/field_tests/<str:test_name>/', views.TestView.as_view()),
]
