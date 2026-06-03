from django.urls import path
from .admin import site
from .views import DashboardStatsView, ProductDetailView

urlpatterns = [
    path("api_admin/", site.urls),
    path("api/dashboard-stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("api/products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
]
