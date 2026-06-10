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
from datetime import datetime

from django.urls import path
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from rest_framework.test import APITestCase, URLPatternsTestCase, APIRequestFactory
from rest_framework.renderers import JSONRenderer

from django_api_admin import APIModelAdmin, site
from django_api_admin.admins.model_admin import TO_FIELD_VAR
from django_api_admin.models import LogEntry

from .models import Product, Trademark, Category, Review, Customer, Contract
from .views import ProductDetailView
from .admin import ProductAdmin

UserModel = get_user_model()
renderer = JSONRenderer()


def setup_tests(test_case):
    test_case.factory = APIRequestFactory()

    # Create a superuser
    test_case.user = UserModel.objects.create_superuser(username="admin")
    test_case.user.set_password("password")
    test_case.user.save()

    # Add model infos
    test_case.product_info = (Product._meta.app_label, Product._meta.model_name)
    test_case.trademark_info = (Trademark._meta.app_label, Trademark._meta.model_name)
    test_case.category_info = (Category._meta.app_label, Category._meta.model_name)

    # Authenticate the superuser
    test_case.client.login(username="admin", password="password")
    test_case.client.force_authenticate(user=test_case.user)

    # Create Some trademarks
    test_case.nike_trademark = Trademark.objects.create(name="Nike")
    test_case.adidas_trademark = Trademark.objects.create(name="Adidas")
    test_case.timberland_trademark = Trademark.objects.create(name="Timberland")

    # Create some categories
    test_case.footwear_category = Category.objects.create(name="Footwear", slug="footwear", description="footwear products")

    # Create some products
    test_case.air_max_product = Product.objects.create(
        name="Air Max",
        price=100,
        stock_status="in_stock",
        trademark=test_case.nike_trademark,
        category=test_case.footwear_category,
    )
    test_case.stan_smith_product = Product.objects.create(
        name="Stan Smith",
        price=100,
        stock_status="in_stock",
        trademark=test_case.adidas_trademark,
        category=test_case.footwear_category,
    )
    test_case.air_force_product = Product.objects.create(
        name="Air Force",
        price=100,
        stock_status="out_of_stock",
        trademark=test_case.nike_trademark,
        category=test_case.footwear_category,
    )
    test_case.timberland_product = Product.objects.create(
        name="Timberland",
        price=200,
        stock_status="in_stock",
        trademark=test_case.timberland_trademark,
        category=test_case.footwear_category,
    )
    test_case.jordan_product = Product.objects.create(
        name="Jordan",
        price=150,
        stock_status="in_stock",
        trademark=test_case.nike_trademark,
        category=test_case.footwear_category,
    )

    # Add a contract
    test_case.product_contract_1 = Contract.objects.create(product=test_case.air_max_product, name="Air Max Contract")

    # Add a customer
    test_case.customer = Customer.objects.create(user=test_case.user)

    # Add some reviews
    test_case.review_bad_air_max = Review.objects.create(
        product=test_case.air_max_product,
        rating=1,
        review_title="Bad product",
        review_content="Very bad product",
        customer=test_case.customer,
    )
    test_case.review_good_air_max = Review.objects.create(
        product=test_case.air_max_product,
        rating=4,
        review_title="Good product",
        review_content="Good product",
        customer=test_case.customer,
    )
    test_case.review_neutral_air_max = Review.objects.create(
        product=test_case.air_max_product,
        rating=3,
        review_title="Not bad product",
        review_content="Not bad product",
        customer=test_case.customer,
    )


class AdminSiteTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api_admin/", site.urls),
        path("product/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    ]

    def setUp(self) -> None:
        setup_tests(self)

    def test_registering_models(self):
        from django.db import models

        class Meta:
            app_label = "django_api_admin"

        # Dynamically create some models and model admins
        student_model = type("Student", (models.Model,), {"__module__": __name__, "Meta": Meta})
        teacher_model = type("Teacher", (models.Model,), {"__module__": __name__, "Meta": Meta})
        teacher_model_admin = type("TeacherModelAdmin", (APIModelAdmin,), {"__module__": __name__, "Meta": Meta})

        # Register the models using the site
        site.register(student_model)
        site.register(teacher_model, teacher_model_admin)

        # Test that the models and modelAdmins are in site._registry
        self.assertIn(student_model, site._registry)
        self.assertIn(teacher_model, site._registry)
        self.assertTrue(isinstance(site._registry[teacher_model], APIModelAdmin))

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
        self.client.force_authenticate(user=user)

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
        content_type_id = ContentType.objects.get(app_label=Product._meta.app_label, model=Product._meta.verbose_name).id
        object_id = Product.objects.first().id
        url = reverse("api_admin:view_on_site", kwargs={"content_type_id": content_type_id, "object_id": object_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["url"], f"http://testserver/{Product._meta.verbose_name}/{object_id}/")
        url = response.data["data"]["url"]
        # Test the detail view
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        product = json.loads(response.content)
        self.assertEqual(product["name"], "Air Max")

    def test_each_context_view(self):
        url = reverse("api_admin:site_context")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["site_title"], "Django site admin")

    def test_autocomplete_view(self):
        # Select a book author by searching for the author using the publisher name of the author
        url = reverse("api_admin:autocomplete")
        response = self.client.get(
            url,
            {
                "term": "Stan",
                "app_label": Product._meta.app_label,
                "model_name": Product._meta.model_name,
                "field_name": "related_products",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["results"][0]["text"], "Stan Smith")


class ModelAdminTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api_admin/", site.urls),
    ]

    def setUp(self) -> None:
        setup_tests(self)

    def test_detail_view(self):
        url = reverse("api_admin:%s_%s_detail" % self.product_info, kwargs={"object_id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["pk"], 1)
        self.assertEqual(response.data["data"]["name"], "Air Max")

    def test_performing_custom_actions(self):
        action_dict = {
            "action": "mark_out_of_stock",
            "selected_ids": [
                1,
            ],
            "select_across": False,
        }

        url = reverse("api_admin:%s_%s_changelist" % self.product_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 200)

    def test_performing_default_action(self):
        action_dict = {
            "action": "delete_selected",
            "selected_ids": [
                3,
            ],
            "select_across": False,
        }
        url = reverse("api_admin:%s_%s_changelist" % self.product_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 200)

    def test_performing_actions_with_select_across(self):
        action_dict = {"action": "apply_ten_percent_discount", "selected_ids": [], "select_across": True}
        url = reverse("api_admin:%s_%s_changelist" % self.product_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 200)

    def test_performing_invalid_actions(self):
        action_dict = {
            "action": "some_weird_action",
            "select_across": 5.0,
        }
        url = reverse("api_admin:%s_%s_changelist" % self.product_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 400)

    def test_delete_view(self):
        url = reverse("api_admin:%s_%s_delete" % self.product_info, kwargs={"object_id": 4})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Product.objects.filter(pk=4).exists())
        self.assertIsNone(response.data)

    def test_delete_view_protected(self):
        url = reverse("api_admin:%s_%s_delete" % self.trademark_info, kwargs={"object_id": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data, {"status": 409})

    def test_delete_view_bad_to_field(self):
        url = reverse("api_admin:%s_%s_delete" % self.product_info, kwargs={"object_id": 1}) + f"?{TO_FIELD_VAR}=name"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Product.objects.filter(pk=1).exists())

    def _assert_product_form_description(self, data):
        form = data["form"]
        self.assertEqual(form["model"], "mock_app.product")
        self.assertEqual(form["readonly_fields"], ["date_created", "average_rating"])
        self.assertEqual(len(form["fields"]), 8)

        # Assert on specific fields
        field_names = [f["name"] for f in form["fields"]]
        self.assertEqual(
            field_names,
            ["name", "category", "trademark", "price", "discount", "discount_price", "stock_status", "description"],
        )

        # Name field
        name_field = form["fields"][0]
        self.assertEqual(name_field["type"], "CharField")
        self.assertEqual(name_field["attrs"]["label"], "Name")
        self.assertEqual(name_field["attrs"]["max_length"], 255)

        # Category field
        category_field = form["fields"][1]
        self.assertEqual(category_field["type"], "PrimaryKeyRelatedField")
        self.assertEqual(category_field["attrs"]["label"], "Category")

        # Price field
        price_field = form["fields"][3]
        self.assertEqual(price_field["type"], "DecimalField")
        self.assertEqual(price_field["attrs"]["max_digits"], 10)
        self.assertEqual(price_field["attrs"]["decimal_places"], 2)

        # Stock status field
        stock_status_field = form["fields"][6]
        self.assertEqual(stock_status_field["type"], "ChoiceField")
        self.assertEqual(
            stock_status_field["attrs"]["choices"],
            {"in_stock": "In Stock", "out_of_stock": "Out of Stock", "pre_order": "Pre-order"},
        )

        # Description field
        description_field = form["fields"][7]
        self.assertEqual(description_field["type"], "CharField")
        self.assertEqual(description_field["attrs"]["style"], {"base_template": "textarea.html"})

        # Fieldsets
        self.assertEqual(form["fieldsets"][0][0], "General Information")
        fields_in_fieldset = form["fieldsets"][0][1]["fields"]
        self.assertIn("name", fields_in_fieldset)
        self.assertIn("average_rating", fields_in_fieldset)

        # Misc admin options
        self.assertEqual(form["autocomplete_fields"], ("related_products",))
        self.assertEqual(form["filter_horizontal"], ("related_products",))

        # Inlines
        self.assertEqual(len(data["inlines"]), 4)

        # Product Image Inline
        image_inline = data["inlines"][0]
        self.assertEqual(image_inline["model"], "mock_app.productimage")
        self.assertEqual(image_inline["extra"], 3)
        self.assertEqual(image_inline["min_num"], 1)
        self.assertEqual(image_inline["max_num"], 1)
        self.assertEqual(image_inline["admin_style"], "tabular")

    def test_add_form_description(self):
        url = reverse("api_admin:%s_%s_add" % self.product_info)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self._assert_product_form_description(data)

        # Permissions
        self.assertTrue(data["form"]["permissions"]["has_add_permission"])

        # Inline formset specific
        image_formset = data["inlines"][0]
        self.assertEqual(len(image_formset["formset"]), 1)
        self.assertEqual(image_formset["formset"][0][0]["type"], "ImageField")

    def test_add_view(self):
        url = reverse("api_admin:%s_%s_add" % self.product_info)
        data = {
            "data": {
                "name": "Duramo SL",
                "category": 1,
                "trademark": 2,
                "price": 199.99,
                "stock_status": "in_stock",
                "description": "The adidas Duramo SL Shoes put some snap into your step with LIGHTMOTION",
            }
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["form"]["name"], "Duramo SL")

        product_id = response.data["data"]["form"]["pk"]
        url = reverse("api_admin:history", query={"app_label": "mock_app", "model": "Product", "object_id": product_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["results"][0]["object_repr"], "Duramo SL")

    def test_change_form_description(self):
        url = reverse("api_admin:%s_%s_change" % self.product_info, kwargs={"object_id": 1})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self._assert_product_form_description(data)

        form = data["form"]
        # Permissions
        self.assertTrue(form["permissions"]["has_change_permission"])

        # # Current values
        self.assertEqual(form["fields"][0]["attrs"]["current_value"], self.air_max_product.name)
        self.assertEqual(form["fields"][1]["attrs"]["current_value"], self.air_max_product.category.pk)

        # Inline formsets
        review_formset = data["inlines"][2]
        self.assertEqual(len(review_formset["formset"]), 4)
        self.assertEqual(review_formset["formset"][0][2]["attrs"]["current_value"], self.review_bad_air_max.rating)
        self.assertEqual(review_formset["formset"][1][2]["attrs"]["current_value"], self.review_good_air_max.rating)
        self.assertNotIn("current_value", review_formset["formset"][3][0]["attrs"])

    def test_change_view(self):
        url = reverse("api_admin:%s_%s_change" % self.product_info, kwargs={"object_id": 1})
        data = {
            "data": {
                "name": "Air Max 2",
                "price": 299.99,
            }
        }
        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["form"]["name"], "Air Max 2")
        self.assertEqual(response.data["data"]["form"]["price"], "299.99")

        url = reverse(
            "api_admin:history",
            query={"app_label": Product._meta.app_label, "model": Product._meta.model_name, "object_id": 1, "page": 1},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data["data"]["results"]) == 1)

    def test_pagination_class(self):
        # Perform some actions then paginate them
        dataset = [
            {
                "name": "Adidas Ultraboost",
                "category": 1,
                "trademark": 2,
                "price": 180.00,
                "stock_status": "in_stock",
                "description": "Adidas Ultraboost Shoes",
            },
            {
                "name": "Adidas Stan Smith",
                "category": 1,
                "trademark": 2,
                "price": 120.00,
                "stock_status": "in_stock",
                "description": "Adidas Stan Smith Shoes",
            },
            {
                "name": "Adidas Gazelle",
                "category": 1,
                "trademark": 2,
                "price": 100.00,
                "stock_status": "in_stock",
                "description": "Adidas Gazelle Shoes",
            },
        ]
        for data in dataset:
            url = reverse("api_admin:%s_%s_add" % self.product_info)
            self.client.post(url, data={"data": data}, format="json")

        url = reverse(
            "api_admin:history",
            query={
                "app_label": Product._meta.app_label,
                "model": Product._meta.model_name,
                "page": 1,
            },
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 3)

    def test_changelist_view(self):
        current_date = datetime.now()

        date_hierarchy = f"date_created__day={current_date.day}"
        f"&date_created__month={current_date.month}"
        f"&date_created__year={current_date.year}"
        ordering = "o=1.-2"
        search = "q=Stan"
        filter = "stock_status__exact=in_stock"
        view_name = f"api_admin:{self.product_info[0]}_{self.product_info[1]}_changelist"
        url = f"{reverse(view_name)}?{date_hierarchy}&{filter}&{ordering}&{search}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["config"]["list_display"], ("name", "category", "price", "stock_status"))
        self.assertEqual(len(response.data["data"]["columns"]), 4)
        self.assertEqual(response.data["data"]["columns"][0]["field"], "name")
        self.assertEqual(response.data["data"]["rows"][0]["cells"]["name"], "Stan Smith")
        self.assertEqual(response.data["data"]["rows"][0]["cells"]["category"], "Footwear")

        data = {"data": [{"pk": 1, "stock_status": "out_of_stock"}]}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], 200)
        self.assertEqual(response.data["data"][0]["stock_status"], "out_of_stock")

    def test_get_serializer_class(self):
        request = self.factory.get("/")
        request.user = self.user
        modeladmin = ProductAdmin(Product, site)
        serializer_class = modeladmin.get_serializer_class(request)
        product = Product.objects.first()
        serializer = serializer_class(product)
        fields = serializer.get_fields()

        self.assertEqual(
            list(fields.keys()),
            [
                "name",
                "category",
                "trademark",
                "price",
                "discount",
                "discount_price",
                "stock_status",
                "average_rating",
                "description",
                "pk",
            ],
        )
        self.assertIsNotNone(fields["discount"].help_text)
        self.assertEqual(serializer.data["category"], 1)
        self.assertIsNone(serializer.data.get("date_created", None))

    def test_get_changelist_serializer_class(self):
        request = self.factory.get("/")
        request.user = self.user
        modeladmin = ProductAdmin(Product, site)
        serializer_class = modeladmin.get_changelist_serializer_class(request)
        products = Product.objects.all()
        serializer = serializer_class(products, many=True)
        fields = serializer.child.get_fields()
        self.assertEqual(list(fields.keys()), ["pk", "stock_status"])
        self.assertEqual(list(fields["stock_status"].choices), ["in_stock", "out_of_stock", "pre_order"])


class InlineAdminTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api_admin/", site.urls),
    ]

    def setUp(self) -> None:
        setup_tests(self)

    def test_inline_bulk_additions(self):
        url = reverse("api_admin:%s_%s_add" % self.product_info)
        data = {
            "data": {
                "name": "Duramo SL",
                "category": 1,
                "trademark": 2,
                "price": 199.99,
                "stock_status": "in_stock",
                "description": "The adidas Duramo SL Shoes put some snap into your step with LIGHTMOTION",
            },
            "inlines": {
                "mock_app.review": {
                    "add": [
                        {
                            "rating": 1,
                            "review_title": "Bad product",
                            "review_content": "Very bad product",
                            "customer": self.customer.pk,
                        },
                        {
                            "rating": 4,
                            "review_title": "Good product",
                            "review_content": "Very good product",
                            "customer": self.customer.pk,
                        },
                    ]
                }
            },
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data["data"]["inlines"])
        self.assertEqual(len(response.data["data"]["inlines"]["mock_app.review"]["add"]), 2)
        self.assertEqual(response.data["data"]["inlines"]["mock_app.review"]["add"][0]["rating"], 1)

    def test_inline_bulk_updates(self):
        url = reverse("api_admin:%s_%s_change" % self.product_info, kwargs={"object_id": self.air_max_product.pk})
        data = {
            "data": {
                "price": 200,
            },
            "inlines": {
                "mock_app.review": {
                    "change": [
                        {
                            "pk": self.review_bad_air_max.pk,
                            "rating": 1,
                            "review_title": "Very Expensive Product",
                            "review_content": "Why is it so expensive now",
                            "customer": self.customer.pk,
                        },
                        {
                            "pk": self.review_good_air_max.pk,
                            "rating": 4,
                            "review_title": "Sudden Price Increase",
                            "review_content": "Why the sudden increase in price?",
                            "customer": self.customer.pk,
                        },
                    ],
                    "delete": [self.review_neutral_air_max.pk],
                },
            },
        }
        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["data"]["inlines"])
        self.assertEqual(len(response.data["data"]["inlines"]["mock_app.review"]["change"]), 2)
        self.assertEqual(
            response.data["data"]["inlines"]["mock_app.review"]["change"][0]["review_title"], "Very Expensive Product"
        )
        self.assertEqual(len(response.data["data"]["inlines"]["mock_app.review"]["delete"]), 1)
        self.assertEqual(response.data["data"]["inlines"]["mock_app.review"]["delete"][0]["review_title"], "Not bad product")

    def test_updating_unrelated_inlines(self):
        url = reverse("api_admin:%s_%s_add" % self.product_info)
        data = {
            "data": {
                "name": "Duramo SL",
                "category": 1,
                "trademark": 2,
                "price": 199.99,
                "stock_status": "in_stock",
                "description": "The adidas Duramo SL Shoes put some snap into your step with LIGHTMOTION",
            },
            "inlines": {"mock_app.technique": {"add": {"2cad3": {"name": "heavenly demon transformation art"}}}},
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response.data["errors"])
        self.assertTrue(isinstance(response.data["errors"]["inlines"]["mock_app.technique"]["non_form_errors"], list))

    def test_invalid_inline_data(self):
        url = reverse("api_admin:%s_%s_add" % self.product_info)
        data = {
            "data": {
                "name": "Alpha Huarache",
                "category": 1,
                "trademark": 2,
                "price": 200.00,
                "stock_status": "in_stock",
                "description": "Men's Alpha Huarache NXT Baseball Cleats",
            },
            "inlines": {
                "mock_app.review": {
                    "add": [
                        {
                            "rating": 2,
                            # Missing review_title
                            "review_content": "Decent, but could be better.",
                            "customer": self.customer.pk,
                        },
                        {
                            "rating": 5,
                            "review_title": "Amazing comfort",
                            "review_content": "The best cleats I have ever worn.",
                            "customer": self.customer.pk,
                        },
                        {
                            "rating": 4,
                            "review_title": "Great performance",
                            "review_content": "Very light and responsive on the field.",
                            "customer": self.customer.pk,
                        },
                        {
                            "rating": 3,
                            "review_title": "Average",
                            "review_content": "Not bad, but I expected more for the price.",
                            "customer": self.customer.pk,
                        },
                        {
                            "rating": 1,
                            "review_title": "Disappointing",
                            "review_content": "Tore after only two games. Very poor quality.",
                            "customer": self.customer.pk,
                        },
                        {
                            "rating": 4,
                            "review_title": "Solid choice",
                            "review_content": "Good traction and fit. Would recommend.",
                            "customer": self.customer.pk,
                        },
                        {
                            # Exceeds the `max_num`
                            "rating": 5,
                            "review_title": "Perfect fit",
                            "review_content": "True to size and very comfortable.",
                            "customer": self.customer.pk,
                        },
                    ],
                    "change": [
                        {
                            # Missing pk
                            "rating": 3,
                            "review_title": "Updated thoughts",
                            "review_content": "After more use, I've adjusted my rating.",
                            "customer": self.customer.pk,
                        }
                    ],
                },
            },
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(isinstance(response.data["errors"]["inlines"]["mock_app.review"]["add"][0], list))
        self.assertTrue(isinstance(response.data["errors"]["inlines"]["mock_app.review"]["change"][0], list))
        self.assertEqual(len(Product.objects.filter(name="Alpha Huarache")), 0)

    def test_changing_unrelated_instance(self):
        url = reverse("api_admin:%s_%s_change" % self.product_info, kwargs={"object_id": self.stan_smith_product.pk})
        data = {
            "data": {},
            "inlines": {
                "mock_app.review": {
                    "change": [
                        {
                            "pk": self.review_bad_air_max.pk,
                            "rating": 1,
                            "review_title": "Very Expensive Product",
                            "review_content": "Why is it so expensive now",
                            "customer": self.customer.pk,
                        },
                    ]
                },
            },
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(isinstance(response.data["errors"]["inlines"]["mock_app.review"]["change"][0], list))

    def test_constructing_change_messages(self):
        url = reverse("api_admin:%s_%s_change" % self.product_info, kwargs={"object_id": self.air_max_product.pk})
        data = {
            "data": {"price": 300},
            "inlines": {
                "mock_app.review": {
                    "add": [
                        {
                            "rating": 5,
                            "review_title": "Highly Recommended",
                            "review_content": "Excellent quality and very durable.",
                            "customer": self.customer.pk,
                        },
                    ],
                    "change": [
                        {
                            "pk": self.review_bad_air_max.pk,
                            "rating": 2,
                            "review_title": "Better than expected",
                            "review_content": "I previously gave a bad review, but it's not that bad.",
                            "customer": self.customer.pk,
                        },
                        {
                            "pk": self.review_good_air_max.pk,
                            "rating": 5,
                            "review_title": "Updated: Still Great",
                            "review_content": "After 6 months, these are still holding up well.",
                            "customer": self.customer.pk,
                        },
                    ],
                    "delete": [self.review_neutral_air_max.pk],
                },
            },
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)

        log_entry = LogEntry.objects.get(object_repr="Air Max")
        change_message = json.loads(log_entry.change_message)
        self.assertEqual(len(change_message), 5)

        self.assertTrue("changed" in change_message[0])
        self.assertEqual(change_message[0]["changed"]["fields"], ["Price"])

        self.assertTrue("added" in change_message[1])
        self.assertEqual(change_message[1]["added"]["object"], "Highly Recommended - 5")

        self.assertTrue("changed" in change_message[2])
        self.assertEqual(change_message[2]["changed"]["object"], "Better than expected - 2")

        self.assertTrue("changed" in change_message[3])
        self.assertEqual(change_message[3]["changed"]["object"], "Updated: Still Great - 5")

        self.assertTrue("deleted" in change_message[4])
        self.assertEqual(change_message[4]["deleted"]["object"], "Not bad product - 3")

    def test_deleting_protected_inline_instance(self):
        url = reverse("api_admin:%s_%s_change" % self.trademark_info, kwargs={"object_id": 1})
        data = {
            "data": {"name": "Nike, Inc."},
            "inlines": {"mock_app.product": {"delete": [1]}},
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            response.data["errors"]["inlines"]["mock_app.product"]["delete"][0][0].startswith(
                (
                    "Deleting product Air Max would require deleting the following protected related"
                    " objects: contract Air Max Contract"
                )
            )
        )
