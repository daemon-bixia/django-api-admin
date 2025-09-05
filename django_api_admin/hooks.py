from django.urls import URLResolver
from django.utils.translation import gettext as _
from django_api_admin.sites import all_sites
from drf_spectacular.settings import spectacular_settings


def tag_paths(urlpatterns, endpoints, site, result, tag_name):
    """
    Tag method of the endpoints in result[paths] with the tag_name after
    checking that this endpoint exists in both the urlpatterns, and the endpoints 
    of the AdminSite, or the ModelAdmin
    """
    for path in urlpatterns:
        for endpoint in endpoints:
            # Extract the endpoint's route representation used in the OpenAPI scheme
            endpoint_url = site.url_prefix + endpoint[0]
            # Check that the endpoint exists in the ModelAdmin's, or AdminSite's OpenAPI endpoints
            if result['paths'].get(endpoint_url, None):
                # Extract the endpoint's route used in the urlpatterns list
                endpoint_url_pattern = endpoint[1][1:] if endpoint[1].startswith(
                    '/') else endpoint[1]
                # If path is instead a URLResolver object try to find the endpoint inside the url_patterns...
                # ...of the URLResolver object
                if isinstance(path, URLResolver):
                    for inner_path in path.url_patterns:
                        inline_url_pattern = str(
                            path.pattern) + str(inner_path.pattern)
                        if inline_url_pattern == endpoint_url_pattern:
                            # Tag all the methods of the endpoint with the tag_name
                            for method, body in result['paths'][endpoint_url].items():
                                result['paths'][endpoint_url][method] = {
                                    **body,
                                    "tags": [tag_name]
                                }
                # Check that the endpoint exists in the ModelAdmin's, or AdminSite's urlpatterns
                elif str(path.pattern) == endpoint_url_pattern:
                    # Tag all the methods of the endpoint with the tag_name
                    for method, body in result['paths'][endpoint_url].items():
                        result['paths'][endpoint_url][method] = {
                            **body,
                            "tags": [tag_name]
                        }
    return result


def modify_schema(result, generator, request, public):
    # Change the api info
    result['info'] = {
        'title': _('Django API Admin'),
        'description': _('A rewrite of django.contrib.admin as a Restful API, intended for use\t'
                         'in the process of creating custom admin panels using frontend frameworks like'
                         'react, and vue while maintaining an API similar to django.contrib.admin.'),
        'contact': 'msbizzacc0unt@gmail.com',
        'license': {
            'name': 'MIT License',
            'url': 'https://github.com/demon-bixia/django-api-admin/blob/production/LICENSE'
        },
        'version': "1.0.0",
    }

    # Edit the tags for each path based on the model_admin or admin_site
    for site in all_sites:
        # Create a generator and parse the site urls so that we can compare them below
        site_generator = spectacular_settings.DEFAULT_GENERATOR_CLASS(
            patterns=site.site_urls)
        site_generator.parse(request, True)
        result = tag_paths(
            site.site_urls,
            site_generator.endpoints,
            site,
            result,
            site.name
        )

        # Update the urls for each registered model
        for model in site._registry.keys():
            model_urls = site.admin_urls.get(model, None)
            if model_urls:
                # Create a generator and parse the admin urls so that we can compare them below
                admin_generator = spectacular_settings.DEFAULT_GENERATOR_CLASS(
                    patterns=model_urls)
                admin_generator.parse(request, True)
                result = tag_paths(
                    model_urls,
                    admin_generator.endpoints,
                    site,
                    result,
                    model._meta.verbose_name
                )

    return result
