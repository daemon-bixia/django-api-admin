from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Order


class DashboardStatsView(APIView):
    def get(self, request):
        return Response({
            "total_products": Product.objects.count(),
            "total_orders": Order.objects.count(),
            "out_of_stock_count": Product.objects.filter(stock_status="out_of_stock").count(),
        })
