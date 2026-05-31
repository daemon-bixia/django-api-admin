from rest_framework import serializers
from .models import Product
from .fields import StockDetailField


class ProductSerializer(serializers.ModelSerializer):
    stock_info = StockDetailField(source="*", required=False)
    read_only_fields = ("stock_status",)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "stock_status",
            "trademark",
            "discount",
            "discount_price",
            "description",
            "related_products",
            "stock_info",
        ]
