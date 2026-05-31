from rest_framework import serializers


class StockDetailField(serializers.Field):
    def to_representation(self, value):
        """Maps stock status to a structured dict for the API."""
        return {
            "status": value.stock_status,
            "is_available": value.stock_status in ["in_stock", "pre_order"],
            "label": dict(value._meta.get_field("stock_status").choices).get(value.stock_status),
        }

    def to_internal_value(self, data):
        """Maps API dict back to model field."""
        return {
            "stock_status": data.get("status"),
        }
