from django.db import models

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import authentication

from django_api_admin import APIAdminSite
from django_api_admin import APIModelAdmin, display, TabularInlineAPI
from django_api_admin.constants import CORE_FIELD_ATTRIBUTES
from django_api_admin.admins.model_admin import ShowFacets

from example.permissions import IsMFAEnabledOrGracePeriod
from example.models import Product, ProductImage, ProductFeature, Metadata, Catalog, Review
from example.actions import mark_out_of_stock


class AdminSite(APIAdminSite):
    def get_authentication_classes(self):
        from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication

        return [XSessionTokenAuthentication, authentication.SessionAuthentication]

    def get_permission_classes(self):
        return [
            IsAuthenticated,
            IsAdminUser,
            IsMFAEnabledOrGracePeriod,
        ]


site = AdminSite(include_auth=True)


class ProductImageInline(TabularInlineAPI):
    model = ProductImage
    min_num = 1
    max_num = 1


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
    min_num = 0
    max_num = 5


class ProductAdmin(APIModelAdmin):
    list_display = ("name", "category", "price", "stock_status")
    list_display_links = ("name",)
    list_filter = ("category", "stock_status")
    list_editable = ("stock_status",)
    list_per_page = 6
    empty_value_display = "-"
    search_fields = (
        "name",
        "description",
        "trademark__name",
    )
    ordering = ("-date_created",)

    filter_horizontal = ("related_products",)
    # raw_id_fields = ("category", )
    autocomplete_fields = ("related_products",)
    date_hierarchy = "date_created"

    serializer_field_overrides = {
        models.DecimalField: {"help_text": "Enter a number (decimals allowed)"},
    }

    serializer_field_attributes = {"LocationField": [*CORE_FIELD_ATTRIBUTES]}

    actions = (mark_out_of_stock,)
    actions_selection_counter = True

    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    "name",
                    (
                        "category",
                        "trademark",
                    ),
                    (
                        "price",
                        "discount",
                        "discount_price",
                    ),
                    "stock_status",
                    "average_rating",
                    "description",
                ),
            },
        ),
    )
    # A list of field names to exclude from the add/change form.
    exclude = ("date_created",)
    readonly_fields = ("date_created", "average_rating")

    inlines = [
        ProductImageInline,
        CatalogInline,
        ReviewInline,
        MetaDataInline,
    ]

    show_facets = ShowFacets.ALWAYS

    @display(description="Average Rating")
    def average_rating(self, obj, context=None) -> float:
        ratings = obj.reviews.values_list("rating", flat=True)
        return sum(ratings) / len(ratings) if ratings else None


# Register your models here
site.register(Product, ProductAdmin)
