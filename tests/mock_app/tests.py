# -----------------------------------------------------------------------------
# Portions of this file are from Django (https://www.djangoproject.com/)
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
# Licensed under the BSD 3-Clause License.
#
# Additional code copyright (c) 2021 Muhammad Salah
# Licensed under the MIT License
#
# This file includes both Django code and your my own contributions.
# -----------------------------------------------------------------------------

import json

from django.urls import path
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from rest_framework.test import APITestCase, URLPatternsTestCase, APIRequestFactory
from rest_framework.renderers import JSONRenderer

from django_api_admin import APIModelAdmin, site

from .models import Product, Trademark, Category
from .views import ProductDetailView

UserModel = get_user_model()
renderer = JSONRenderer()


class AdminSiteTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api_admin/", site.urls),
        path("product/<int:pk>/",
             ProductDetailView.as_view(), name="product-detail"),
    ]

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

        # Create a superuser
        self.user = UserModel.objects.create_superuser(username="admin")
        self.user.set_password("password")
        self.user.save()

        # Authenticate the superuser
        self.client.login(username="admin", password="password")
        self.client.force_authenticate(user=self.user)

        # Create Some trademarks
        self.nike_trademark = Trademark.objects.create(name="Nike")
        self.adidas_trademark = Trademark.objects.create(name="Adidas")

        # Create some categories
        self.footwear_category = Category.objects.create(name="Footwear", slug="footwear",
                                                         description="footwear products")

        # Create some products
        self.air_max_product = Product.objects.create(name="Air Max", price=100,
                                                      stock_status="in_stock", trademark=self.nike_trademark,
                                                      category=self.footwear_category)
        self.stan_smith_product = Product.objects.create(name="Stan Smith", price=100,
                                                         stock_status="in_stock", trademark=self.adidas_trademark,
                                                         category=self.footwear_category)

    def test_registering_models(self):
        from django.db import models

        class Meta:
            app_label = "django_api_admin"

        # Dynamically create some models and model admins
        student_model = type("Student", (models.Model,),
                             {"__module__": __name__, "Meta": Meta})
        teacher_model = type("Teacher", (models.Model,),
                             {"__module__": __name__, "Meta": Meta})
        teacher_model_admin = type("TeacherModelAdmin", (APIModelAdmin,), {
                                   "__module__": __name__, "Meta": Meta})

        # Register the models using the site
        site.register(student_model)
        site.register(teacher_model, teacher_model_admin)

        # Test that the models and modelAdmins are in site._registry
        self.assertIn(student_model, site._registry)
        self.assertIn(teacher_model, site._registry)
        self.assertTrue(isinstance(
            site._registry[teacher_model], APIModelAdmin))

    def test_app_list_serializable(self):
        # Force superuser authentication
        request = self.factory.get("index/")
        request.user = self.user
        # Test if app_list can be serialized to json
        data = renderer.render(site.get_app_list(request))
        self.assertIsNotNone(data)

    def test_each_context_serializable(self):
        # Force superuser authentication
        request = self.factory.get("index/")
        request.user = self.user
        # Test if context can be serialized to json
        data = renderer.render(site.each_context(request))
        self.assertIsNotNone(data)

    def test_index_view(self):
        # Test if the index view works
        url = reverse("api_admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_app_index_view(self):
        # Test if the app_index view works
        app_label = Product._meta.app_label
        url = reverse("api_admin:app_index", kwargs={"app_label": app_label})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_permission_denied(self):
        # Create a non-staff user
        user = UserModel.objects.create(username="guest")
        user.set_password("password")
        user.is_staff = False
        user.save()

        # Authenticate the superuser
        self.client.login(username="guest", password="password")
        self.client.force_authenticate(user=self.user)

        # Test if app_index denies permission
        app_label = Product._meta.app_label
        url = reverse("api_admin:app_index", kwargs={"app_label": app_label})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # Test if index denies permission
        url = reverse("api_admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_view_on_site_view(self):
        # Test if view_on_site view works
        content_type_id = ContentType.objects.get(
            app_label=Product._meta.app_label, model=Product._meta.verbose_name).id
        object_id = Product.objects.first().id
        url = reverse("api_admin:view_on_site", kwargs={
            "content_type_id": content_type_id, "object_id": object_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["url"], f"http://testserver/{Product._meta.verbose_name}/{object_id}/")
        url = response.data["url"]
        # Test the detail view
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        product = json.loads(response.content)
        self.assertEqual(product["name"], "Air Max")

    def test_each_context_view(self):
        url = reverse("api_admin:site_context")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["site_title"], "Django site admin")

    def test_autocomplete_view(self):
        # Select a book author by searching for the author using the publisher name of the author
        url = reverse("api_admin:autocomplete")
        response = self.client.get(url, {
            "term": "Stan",
            "app_label": Product._meta.app_label,
            "model_name": Product._meta.model_name,
            "field_name": "related_products"
        })
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["text"], "Stan Smith")
