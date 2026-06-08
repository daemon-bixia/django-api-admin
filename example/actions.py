from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response

from django_api_admin.decorators import action


@action(description=_("Mark selected products as out of stock"))
def mark_out_of_stock(model_admin, request, queryset):
    return Response(
        {"status": status.HTTP_200_OK},
        status=status.HTTP_200_OK,
    )
