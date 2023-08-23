"""
model admin tests.
"""
import json

from django.contrib.auth import get_user_model
from django.urls import path, reverse

from rest_framework.test import (APIRequestFactory, APITestCase,
                                 URLPatternsTestCase)

from django_api_admin.models import Author, Publisher
from django_api_admin.sites import site

UserModel = get_user_model()


class ModelAdminTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api_admin/', site.urls),
    ]

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

        # create a superuser
        self.user = UserModel.objects.create_superuser(username='admin')
        self.user.set_password('password')
        self.user.save()

        # authenticate the superuser
        self.client.force_login(user=self.user)

        # create some valid authors
        Author.objects.create(name="muhammad", age=20,
                              is_vip=True, user_id=self.user.pk)
        Author.objects.create(name="Ali", age=20,
                              is_vip=False, user_id=self.user.pk)
        Author.objects.create(name="Omar", age=60,
                              is_vip=True, user_id=self.user.pk)
        self.author_info = (Author._meta.app_label, Author._meta.model_name)

        # create some valid publishers
        Publisher.objects.create(name='rock')
        Publisher.objects.create(name='paper')
        Publisher.objects.create(name='scissor')

    def test_list_view(self):
        url = reverse('api_admin:%s_%s_list' % self.author_info)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'muhammad')

    def test_detail_view(self):
        url = reverse('api_admin:%s_%s_detail' %
                      self.author_info, kwargs={'object_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'muhammad')

    def test_autocomplete_views(self):
        # GET /admin/autocomplete/?term=p&app_label=django_api_admin&model_name=author&field_name=publisher
        url = reverse(
            'api_admin:autocomplete') + '?term=r&app_label=django_api_admin&model_name=author&field_name=publisher'
        response = self.client.get(url)
        data = json.loads(response.data['content'])
        self.assertEqual(int(data['results'][0]['id']), 1)

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
        self.author_info = (Author._meta.app_label, Author._meta.model_name)
        url = reverse('api_admin:%s_%s_perform_action' % self.author_info)
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
            'action': 'some_weird_action',
            'select_across': 5.0,
        }
        url = reverse('api_admin:%s_%s_perform_action' % self.author_info)
        response = self.client.post(url, data=action_dict)
        self.assertEqual(response.status_code, 400)

    def test_delete_view(self):
        author = Author.objects.create(
            name="test", age=20, is_vip=True, user_id=self.user.pk)
        url = reverse('api_admin:%s_%s_delete' %
                      self.author_info, kwargs={'object_id': author.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Author.objects.filter(pk=author.pk).exists())
        self.assertEqual(
            response.data['detail'], 'The author “test” was deleted successfully.')

    def test_delete_view_bad_to_field(self):
        author = Author.objects.create(
            name="test2", age=20, is_vip=True, user_id=self.user.pk)
        url = reverse('api_admin:%s_%s_delete' % self.author_info, kwargs={
                      'object_id': author.pk}) + '?_to_field=name'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Author.objects.filter(pk=author.pk).exists())
        self.assertEqual(response.data['detail'],
                         'The field name cannot be referenced.')

    def test_add_view(self):
        url = reverse('api_admin:%s_%s_add' % self.author_info)
        data = {
            'data': {
                'name': 'test4',
                'age': 60,
                'is_vip': True,
                'user': self.user.pk,
            }
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['name'], 'test4')

        author_id = response.data['data']['pk']
        url = reverse('api_admin:%s_%s_history' %
                      self.author_info, kwargs={'object_id': author_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['object_repr'], 'test4')

    def test_change_view(self):
        author = Author.objects.create(
            name='hassan', age=60, is_vip=False, user_id=self.user.pk)
        url = reverse('api_admin:%s_%s_change' %
                      self.author_info, kwargs={'object_id': author.pk})
        data = {
            'data': {
                'name': 'muhammad',
                'age': '60',
                'is_vip': True
            }
        }
        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['name'], 'muhammad')

        url = reverse('api_admin:%s_%s_history' % self.author_info,
                      kwargs={'object_id': author.id}) + '?p=1&page_size=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) == 1)

    def test_pagination_class(self):
        # perform some actions then paginate them
        authors = [
            {
                'name': 'test1',
                'age': '60',
                'is_vip': True,
                'user': self.user.pk
            },
            {
                'name': 'test2',
                'age': '60',
                'is_vip': True,
                'user': self.user.pk
            },
            {
                'name': 'test3',
                'age': '60',
                'is_vip': True,
                'user': self.user.pk
            },
        ]
        for author in authors:
            url = reverse('api_admin:%s_%s_add' % self.author_info)
            self.client.post(url, data={'data': author}, format="json")

        url = reverse('api_admin:admin_log') + '?page_size=1&p=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['action_list']), 1)
