from datetime import datetime

from django.contrib.auth import get_user_model
from django.urls import include, path, reverse

from rest_framework.test import (APIRequestFactory, APITestCase,
                                 URLPatternsTestCase)

from allauth.account.models import EmailAddress

from test_django_api_admin.models import Author, Publisher, Category, Article, Book
from test_django_api_admin.admin import site, AuthorAPIAdmin
from test_django_api_admin import views
from test_django_api_admin.utils import login

from django_api_admin.admins.model_admin import TO_FIELD_VAR


UserModel = get_user_model()


class ModelAdminTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api_admin/', site.urls),
        path('_allauth/', include('allauth.headless.urls')),
        path('api/publisher/<int:pk>/',
             views.PublisherDetailView.as_view(), name="publisher-detail"),
    ]

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

        # Create a superuser
        self.user = UserModel.objects.create_superuser(
            username="admin", email="admin@email.com")
        self.user.set_password("password")
        self.user.save()

        # Verify the user's email
        EmailAddress.objects.create(
            user=self.user,
            email="admin@email.com",
            verified=True,
            primary=True,
        )

        # Authenticate the superuser
        login(self.client, self.user)

        # Create some authors
        Author.objects.create(name="muhammad", age=60,
                              is_vip=True, user_id=self.user.pk)
        Author.objects.create(name="Ali", age=20,
                              is_vip=False, user_id=self.user.pk)
        Author.objects.create(name="Omar", age=60,
                              is_vip=True, user_id=self.user.pk)
        self.author_info = (Author._meta.app_label, Author._meta.model_name)

        # Create some publishers
        Publisher.objects.create(name="rock")
        Publisher.objects.create(name="paper")
        Publisher.objects.create(name="scissor")

    def test_list_view(self):
        url = reverse("api_admin:%s_%s_list" % self.author_info)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["object_list"][0]["name"], "muhammad")

    def test_detail_view(self):
        url = reverse("api_admin:%s_%s_detail" %
                      self.author_info, kwargs={"object_id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], 1)
        self.assertEqual(response.data["name"], "muhammad")
        self.assertTrue(isinstance(response.data["list_url"], str))
        self.assertTrue(isinstance(response.data["delete_url"], str))
        self.assertTrue(isinstance(response.data["change_url"], str))
        self.assertTrue(isinstance(response.data["view_on_site_url"], str))

    def test_performing_custom_actions(self):
        action_dict = {
            'action': 'make_old',
            'selected_ids': [
                1,
                2
            ],
            'select_across': False,
        }

        self.author_info = (Author._meta.app_label, Author._meta.model_name)
        url = reverse('api_admin:%s_%s_perform_action' % self.author_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code,  200)

    def test_performing_actions(self):
        action_dict = {
            'action': 'delete_selected',
            'selected_ids': [
                1,
                2
            ],
            'select_across': False,
        }
        url = reverse("api_admin:%s_%s_changelist" % self.author_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 200)

    def test_performing_actions_with_select_across(self):
        action_dict = {
            'action': 'delete_selected',
            'selected_ids': [],
            'select_across': True
        }
        url = reverse('api_admin:%s_%s_perform_action' % self.author_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Author.objects.all().exists(), False)

    def test_performing_actions_invalid_request(self):
        action_dict = {
            "action": "some_weird_action",
            "select_across": 5.0,
        }
        url = reverse("api_admin:%s_%s_perform_action" % self.author_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 400)

    def test_delete_view(self):
        author = Author.objects.create(
            name="test", age=20, is_vip=True, user_id=self.user.pk)
        url = reverse("api_admin:%s_%s_delete" %
                      self.author_info, kwargs={"object_id": author.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Author.objects.filter(pk=author.pk).exists())
        self.assertEqual(
            response.data["detail"], "The author “test” was deleted successfully.")

    def test_delete_view_protected(self):
        category = Category.objects.create(name="software")
        Article.objects.create(
            title="Best programming languages", category=category)
        url = reverse("api_admin:%s_%s_delete" %
                      (Category._meta.app_label, Category._meta.model_name),
                      kwargs={"object_id": category.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Cannot delete category")

    def test_delete_view_bad_to_field(self):
        author = Author.objects.create(
            name="test2", age=20, is_vip=True, user_id=self.user.pk)
        url = reverse("api_admin:%s_%s_delete" % self.author_info, kwargs={
            "object_id": author.pk}) + f"?{TO_FIELD_VAR}=name"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Author.objects.filter(pk=author.pk).exists())

    def _assert_author_form_description(self, data):
        form = data["form"]
        self.assertEqual(form["model"], "test_django_api_admin.author")
        self.assertEqual(form["readonly_fields"], [
                         "date_joined", "is_old_enough"])
        self.assertEqual(len(form["fields"]), 6)

        # Assert on specific fields
        field_names = [f["name"] for f in form["fields"]]
        self.assertEqual(
            field_names, ["name", "age", "is_vip", "user", "publisher", "location"])

        # Name field details
        name_field = form["fields"][0]
        self.assertEqual(name_field["type"], "CharField")
        self.assertEqual(name_field["attrs"]["label"], "Name")
        self.assertEqual(name_field["attrs"]["help_text"],
                         "This is a custom help text for all CharFields")
        self.assertEqual(name_field["attrs"]["max_length"], 100)

        # Age field - ChoiceField
        age_field = form["fields"][1]
        self.assertEqual(age_field["type"], "ChoiceField")
        self.assertEqual(age_field["attrs"]["choices"], {
                         60: 'senior', 1: 'baby', 2: 'also a baby'})

        # Publisher - ManyRelatedField
        publisher_field = form["fields"][4]
        self.assertEqual(publisher_field["type"], "ManyRelatedField")
        self.assertEqual(publisher_field["attrs"]["label"], "Publisher")

        # Fieldsets
        self.assertEqual(form["fieldsets"][0][0], "Information")
        self.assertIn("is_old_enough", form["fieldsets"][0][1]["fields"])

        # Misc admin options
        self.assertEqual(form["raw_id_fields"], ("publisher",))
        self.assertEqual(form["autocomplete_fields"], ("publisher",))
        self.assertTrue(form["save_as_continue"])
        self.assertTrue(form["view_on_site"])

        # Inline formsets
        self.assertEqual(len(data["inlines"]), 1)
        book_formset = data["inlines"][0]
        self.assertEqual(book_formset["model"], "test_django_api_admin.book")
        self.assertEqual(book_formset["extra"], 3)
        self.assertEqual(book_formset["admin_style"], "tabular")

    def test_add_form_description(self):
        url = reverse('api_admin:%s_%s_add' % self.author_info)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.data
        self._assert_author_form_description(data)

        # Permissions
        self.assertTrue(data["form"]["permissions"]["has_add_permission"])

        # Inline formset specific
        book_formset = data["inlines"][0]
        self.assertEqual(len(book_formset["formset"]), 1)
        self.assertEqual(book_formset["formset"][0][0]["type"], "CharField")

    def test_add_view(self):
        url = reverse('api_admin:%s_%s_add' % self.author_info)
        data = {
            'data': {
                'name': 'test4',
                'age': 60,
                'is_vip': True,
                'user': self.user.pk,
                'publisher': [reverse("publisher-detail", kwargs={"pk": 1})]
            }
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['name'], 'test4')

        author_id = response.data["data"]["pk"]
        url = reverse("api_admin:history", query={
            "app_label": "test_django_api_admin",
            "model": "Author", "object_id": author_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["object_list"]
                         [0]["object_repr"], "test4")

    def test_change_form_description(self):
        author = Author.objects.get(pk=1)
        book_1 = Book.objects.create(
            title="Spice and Wolf, Vol. 1", author=author)
        book_2 = Book.objects.create(
            title="Spice and Wolf, Vol. 2", author=author)
        url = reverse('api_admin:%s_%s_change' %
                      self.author_info, kwargs={'object_id': author.pk})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.data
        self._assert_author_form_description(data)

        form = data["form"]
        # Permissions
        self.assertTrue(form["permissions"]["has_change_permission"])

        # Current values
        self.assertEqual(form["fields"][0]["attrs"]
                         ["current_value"], author.name)
        self.assertEqual(form["fields"][1]["attrs"]
                         ["current_value"], author.age)

        # Inline formsets
        book_formset = data["inlines"][0]
        self.assertEqual(len(book_formset["formset"]), 3)
        # First book title (CharField)
        self.assertEqual(book_formset["formset"][0]
                         [0]["attrs"]["current_value"], book_1.title)
        # Second book title
        self.assertEqual(book_formset["formset"][1]
                         [0]["attrs"]["current_value"], book_2.title)
        # Third form (extra) should not have current_value
        self.assertNotIn(
            "current_value", book_formset["formset"][2][0]["attrs"])

    def test_change_view(self):
        author = Author.objects.create(
            name="hassan", age=60, is_vip=False, user_id=self.user.pk)
        url = reverse("api_admin:%s_%s_change" %
                      self.author_info, kwargs={"object_id": author.pk})
        data = {
            "data": {
                "name": "muhammad",
                "age": "60",
                "is_vip": True,
                "publisher": [reverse("publisher-detail", kwargs={"pk": 1})]
            }
        }
        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "muhammad")

        url = reverse("api_admin:history", query={
            "app_label": "test_django_api_admin",
            "model": "Author", "object_id": author.id,
                      "page": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data["object_list"]) == 1)

    def test_pagination_class(self):
        # perform some actions then paginate them
        dataset = [
            {
                "name": "test1",
                "age": "60",
                "is_vip": True,
                "user": self.user.pk,
                "publisher": [reverse("publisher-detail", kwargs={"pk": 1})]
            },
            {
                "name": "test2",
                "age": "60",
                "is_vip": True,
                "user": self.user.pk,
                "publisher": [reverse("publisher-detail", kwargs={"pk": 1})]
            },
            {
                "name": "test3",
                "age": "60",
                "is_vip": True,
                "user": self.user.pk,
                "publisher": [reverse("publisher-detail", kwargs={"pk": 1})]
            },
        ]
        for data in dataset:
            url = reverse("api_admin:%s_%s_add" % self.author_info)
            self.client.post(url, data={"data": data}, format="json")

        url = reverse("api_admin:history", query={
            "app_label": "test_django_api_admin",
            "model": "Author", "page": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["object_list"]), 3)

    def test_changelist_view(self):
        current_date = datetime.now()

        date_hierarchy = f"date_joined__day={current_date.day}"
        f"&date_joined__month={current_date.month}"
        f"&date_joined__year={current_date.year}"
        ordering = "o=1.-2"
        search = "q=muhammad"
        filter = "is_vip__exact=1"
        view_name = f"api_admin:{self.author_info[0]}_{self.author_info[1]}_changelist"
        url = f"{reverse(view_name)}?{date_hierarchy}&{filter}&{ordering}&{search}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["config"]["list_display"], (
            "name", "age", "user", "is_old_enough", "title", "gender", "date_joined"))
        self.assertEqual(len(response.data["columns"]), 6)
        self.assertEqual(response.data["columns"][0]["field"], "name")
        self.assertEqual(response.data["rows"][0]["cells"]["name"], "muhammad")
        self.assertEqual(
            response.data["rows"][0]["cells"]["age"]["attrs"]["current_value"], 60)

        data = {
            "data": [{
                "pk": 1,
                "name": "Zhuo Fan",
                "age": 2,
            }]
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"],
                         "1 author was changed successfully.")
        self.assertEqual(response.data["data"][1]["age"], 2)

    def test_get_serializer_class(self):
        request = self.factory.get('/')
        request.user = self.user
        modeladmin = AuthorAPIAdmin(Author, site)
        serializer_class = modeladmin.get_serializer_class(request)
        author = Author.objects.first()
        serializer = serializer_class(author)
        fields = serializer.get_fields()

        self.assertEqual(list(fields.keys()), [
                         "name", "age", "is_vip", "user",
                         "publisher", "is_old_enough", "date_joined",
                         "location", "pk"])
        self.assertIsNotNone(fields["name"].help_text)
        self.assertTrue(serializer.data["is_old_enough"])
        self.assertTrue(isinstance(serializer.data["date_joined"], str))

    def test_get_changelist_serializer_class(self):
        request = self.factory.get("/")
        request.user = self.user
        modeladmin = AuthorAPIAdmin(Author, site)
        serializer_class = modeladmin.get_changelist_serializer_class(request)
        author = Author.objects.all()
        serializer = serializer_class(author, many=True)
        fields = serializer.child.get_fields()
        self.assertEqual(list(fields.keys()), ["age"])
        self.assertEqual(list(fields["age"].choices), [60, 1, 2])
