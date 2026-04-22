import copy

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.response import Response


class ListView(APIView):
    """
    Return a list containing all instances of this model.
    """

    serializer_class = None
    permission_classes = []
    model_admin = None

    paginate_orphans = 0
    page_kwarg = "page"
    allow_empty = True
    paginate_by = 20

    def get(self, request):
        queryset = self.model_admin.get_queryset(request)
        paginator = self.model_admin.get_paginator(
            queryset,
            self.paginate_by,
            self.paginate_orphans,
            self.allow_empty,
        )
        page, queryset, is_paginated = self.model_admin.admin_site.paginate_queryset(
            request,
            paginator,
            self.page_kwarg
        )
        serializer = self.serializer_class(queryset, many=True)
        data = copy.deepcopy(serializer.data)
        info = (
            self.model_admin.admin_site.name,
            self.model_admin.model._meta.app_label,
            self.model_admin.model._meta.model_name
        )
        pattern = "%s:%s_%s_detail"
        for item in data:
            item["detail_url"] = reverse(pattern % info, kwargs={
                                         "object_id": item["pk"]}, request=request)

        return Response({
            "num_pages": paginator.num_pages,
            "count": paginator.count,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
            "object_list": data,
        }, status=status.HTTP_200_OK)
