# from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication

from django_api_admin.serializers import AppListSerializer
from django_api_admin.openapi import CommonAPIResponses


class AppListView(APIView):
    """
    Return json object that lists all the installed
    apps that have been registered by the admin site.
    """
    permission_classes = []
    authentication_classes = [XSessionTokenAuthentication,]
    admin_site = None

    @classmethod
    def as_view(cls, **initkwargs):
        if not len(initkwargs.get('authentication_classes', [])): 
            initkwargs['authentication_classes'] = cls.authentication_classes
        return super().as_view(**initkwargs)

    @extend_schema(
        operation_id="admin_root",
        responses={
            200: AppListSerializer,
            403: CommonAPIResponses.permission_denied(),
            401: CommonAPIResponses.unauthorized()
        },
    )
    def get(self, request):
        app_list = self.admin_site.get_app_list(request)
        # add an url to app_index in every app in app_list
        for app in app_list:
            app['url'] = reverse(f'{self.admin_site.name}:app_index', kwargs={
                                 'app_label': app['app_label']}, request=request)
        data = {'app_list': app_list}
        request.current_app = self.admin_site.name
        return Response(data, status=status.HTTP_200_OK)
