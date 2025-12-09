from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django_api_admin.openapi import CommonAPIResponses, APIResponseExamples
from django_api_admin.serializers import APIRootSerializer


class AdminAPIRootView(APIView):
    """
    A list of urls that act as a starting point for browsing the REST API 
    """
    root_urls = None
    admin_site = None

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description=_(
                    "A list of urls that act as a starting point for browsing the REST API"),
                response=APIRootSerializer,
                examples=[APIResponseExamples.root_urls()]
            ),
            401: CommonAPIResponses.unauthorized()
        }
    )
    def get(self, request, ):
        namespace = request.resolver_match.namespace
        data = dict()

        for url in self.root_urls:
            # Include the app_index url for every app
            if url.name == 'app_index':
                valid_app_labels = set(model._meta.app_label for model,
                                       _ in self.admin_site._registry.items())
                for app_label in valid_app_labels:
                    data[f'{app_label}_{url.name}'] = reverse(
                        f'{namespace}:{url.name}',  kwargs={"app_label": app_label}, request=request)

            # Include the rest of the urls except the view_on_site
            # todo: consider including the view_on_site url index every object's detail view response
            elif url.name != "view_on_site":
                data[url.name] = reverse(
                    f'{namespace}:{url.name}', request=request)

        return Response(data or {}, status=status.HTTP_200_OK)
