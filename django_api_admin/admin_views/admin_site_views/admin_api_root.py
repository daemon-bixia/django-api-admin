from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse


class AdminAPIRootView(APIView):
    """
    A list of all root urls in django_api_admin
    """
    root_urls = None
    admin_site = None

    def get(self, request, ):
        namespace = request.resolver_match.namespace
        data = dict()

        for url in self.root_urls:
            # include the app_index url for every app
            if url.name == 'app_index':
                valid_app_labels = set(model._meta.app_label for model,
                                       _ in self.admin_site._registry.items())
                for app_label in valid_app_labels:
                    data[f'{url.name}_{app_label}'] = reverse(
                        namespace + ':' + url.name,  kwargs={"app_label": app_label}, request=request)

            # include the rest of the urls
            elif url.name != "view_on_site":
                data[url.name] = reverse(
                    namespace + ':' + url.name, request=request)

        return Response(data or {}, status=status.HTTP_200_OK)
