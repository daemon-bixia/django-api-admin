from django.utils.translation import gettext_lazy as _
from rest_framework import status
from decimal import Decimal
from rest_framework.response import Response
from django_api_admin.decorators import action


@action(description=_("Mark selected products as out of stock"))
def mark_out_of_stock(modeladmin, request, queryset):
    updated = queryset.update(stock_status="out_of_stock")
    return Response({"detail": _("Successfully marked %d products as out of stock.") % updated}, status=status.HTTP_200_OK)


@action(description=_("Apply 10%% discount to selected products"))
def apply_ten_percent_discount(modeladmin, request, queryset):
    for product in queryset:
        product.discount = Decimal("10.00")
        product.discount_price = product.price * Decimal("0.10")
        product.save()

    return Response(
        {"detail": _("Successfully applied 10%% discount to %d products.") % queryset.count()}, status=status.HTTP_200_OK
    )
