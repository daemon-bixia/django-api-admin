from django.urls import path
from django.db import models

from django_api_admin import APIModelAdmin, APIAdminSite, display, TabularInlineAPI
from django_api_admin.constants import CORE_FIELD_ATTRIBUTES
from django_api_admin.admins.model_admin import ShowFacets

from .models import Product, ProductImage, ProductFeature, Metadata, Catalog, Review
from .views import DashboardStatsView
from .serializers import ProductSerializer
from .actions import mark_out_of_stock, apply_ten_percent_discount


class AdminSite(APIAdminSite):
    def dashboard_stats_view(self, request):
        return DashboardStatsView.as_view()(request)

    def get_urls(self):
        urlpatterns = super(AdminSite, self).get_urls()
        urlpatterns.append(
            path("dashboard/stats/", self.dashboard_stats_view, name="dashboard-stats"))
        return urlpatterns


class ProductImageInline(TabularInlineAPI):
    model = ProductImage
    min_num = 1
    max_num = 1


class RelatedProductInline(TabularInlineAPI):
    model = Product.related_products.through
    min_num = 0
    max_num = 5
    filter_horizontal = ("related_products",)


class ProductFeatureInline(TabularInlineAPI):
    model = ProductFeature
    min_num = 0
    max_num = 5


class MetaDataInline(TabularInlineAPI):
    model = Metadata


class CatalogInline(TabularInlineAPI):
    model = Catalog


class ReviewInline(TabularInlineAPI):
    model = Review


class ProductAdmin(APIModelAdmin):
    serializer_class = ProductSerializer

    list_display = ("name", "category", "price", "stock_status")
    list_display_links = ("name",)
    list_filter = ("category", "stock_status")
    list_editable = ("stock_status",)
    list_per_page = 6
    empty_value_display = "-"
    search_fields = ("name", "description", "trademark",)
    ordering = ("-date_created",)

    # filter_horizontal = ("related_products",)
    # raw_id_fields = ("category", )
    autocomplete_fields = ("related_products",)
    date_hierarchy = "date_created"

    serializer_field_overrides = {
        models.DecimalField: {"help_text": "Enter a number (decimals allowed)"},
    }

    serializer_field_attributes = {
        "LocationField": [*CORE_FIELD_ATTRIBUTES]
    }

    actions = (mark_out_of_stock, apply_ten_percent_discount)
    actions_selection_counter = True

    fieldsets = (
        ("General Information", {
            "fields": ("name", ("category", "trademark",),
                       ("price", "discount", "discount_price",),
                       "stock_status", "average_rating", "description",), }),
    )
    # A list of field names to exclude from the add/change form.
    exclude = ("date_created",)
    readonly_fields = ("date_created", "average_rating")

    inlines = [ProductImageInline, RelatedProductInline,
               CatalogInline, ReviewInline, MetaDataInline,]

    show_facets = ShowFacets.ALWAYS

    @display(description="Average Rating")
    def average_rating(self, obj, context=None) -> float:
        ratings = obj.reviews.values_list("rating", flat=True)
        return sum(ratings) / len(ratings) if ratings else None


# Register your models here
site = AdminSite()
site.register(Product, ProductAdmin)
