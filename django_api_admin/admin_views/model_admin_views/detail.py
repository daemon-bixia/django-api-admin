import copy

from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView

from django_api_admin.utils.quote import unquote
from django_api_admin.constants import TO_FIELD_VAR


class DetailView(APIView):
    """
    GET one instance of this model using pk and to_fields.
    """
    serializer_class = None
    permission_classes = []
    model_admin = None

    def get(self, request, object_id):
        # Validate the reverse to field reference
        to_field = request.query_params.get(TO_FIELD_VAR)
        if to_field and not self.model_admin.to_field_allowed(request, to_field):
            return Response({'detail': _('The field %s cannot be referenced.') % to_field},
                            status=status.HTTP_400_BAD_REQUEST)
        obj = self.model_admin.get_object(
            request, unquote(object_id), to_field)

        # If the object doesn't exist respond with not found
        if obj is None:
            msg = _("%(name)s with ID “%(key)s” doesn't exist. Perhaps it was deleted?") % {
                'name': self.model_admin.model._meta.verbose_name,
                'key': unquote(object_id),
            }
            return Response({'detail': msg}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(obj)
        data = copy.deepcopy(serializer.data)

        pattern = '%s:%s_%s_'
        info = (
            self.model_admin.admin_site.name,
            self.model_admin.model._meta.app_label,
            self.model_admin.model._meta.model_name,
        )

        # Add admin urls.
        data['list_url'] = reverse(
            (pattern + 'list') % info, request=request)
        data['history_url'] = reverse(
            (pattern + 'history') % info, kwargs={'object_id': data['pk']}, request=request)
        data['delete_url'] = reverse(
            (pattern + 'delete') % info, kwargs={'object_id': data['pk']}, request=request)
        data['change_url'] = reverse(
            (pattern + 'change') % info, kwargs={'object_id': data['pk']}, request=request)
        if self.model_admin.view_on_site:
            data['view_on_site_url'] = self.model_admin.get_view_on_site_url(
                obj)

        return Response(data, status=status.HTTP_200_OK)
