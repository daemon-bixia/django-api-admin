from django.contrib.auth import get_user_model
from django.urls import include, path, reverse

from rest_framework.test import (APITestCase,
                                 URLPatternsTestCase)

from allauth.account.models import EmailAddress

from test_django_api_admin.models import Author, Book, Publisher
from test_django_api_admin.admin import site
from test_django_api_admin.utils import login

UserModel = get_user_model()


class InlineModelAdminTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api_admin/', site.urls),
        path('_allauth/', include('allauth.headless.urls')),
    ]

    def setUp(self) -> None:
        # Create a superuser
        self.user = UserModel.objects.create_superuser(
            username='admin', email="admin@email.com")
        self.user.set_password('password')
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

        # Create some valid authors
        self.a1 = Author.objects.create(
            name="Baumgartner", age=20, is_vip=True, user_id=self.user.pk)
        self.a2 = Author.objects.create(
            name="Richard Dawkins", age=20, is_vip=False, user_id=self.user.pk)
        self.a3 = Author.objects.create(
            name="Allen carr", age=60, is_vip=True, user_id=self.user.pk)
        self.author_info = (Author._meta.app_label, Author._meta.model_name)

        # Create a valid publisher
        Publisher.objects.create(name='rock')

        # Create some valid Books
        self.a1_b1 = Book.objects.create(
            title='High performance django', author=self.a1)
        self.a1_b2 = Book.objects.create(
            title='Clean architecture', author=self.a1)
        self.a1_b3 = Book.objects.create(title='Pro git', author=self.a1)
        self.a2_b1 = Book.objects.create(
            title='A devils chaplain', author=self.a2)
        self.a3_b1 = Book.objects.create(
            title='Easy way to stop smoking', author=self.a3)
        self.book_info = (*self.author_info,
                          Book._meta.app_label, Book._meta.model_name)

    def test_inline_bulk_additions(self):
        url = reverse('api_admin:%s_%s_add' % self.author_info)
        data = {
            "data": {
                "name": "Sergei Brin",
                "age": 60,
                "user": self.user.pk,
                "is_vip": False,
                'publisher': [1]
            },
            "inlines": {
                "test_django_api_admin/book": {
                    "add": {
                        "j18ca": {
                            "title": "The freedom model",
                            "credits": [self.a1.pk]
                        },
                        "a92b#": {
                            "title": "API security oauth2 and beyond",
                            "credits": [self.a1.pk]
                        },
                        "$3fv2": {
                            "title": "OpenId connect in action",
                            "credits": [self.a1.pk]
                        }
                    }
                }
            }
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data.get("inlines"))
        self.assertEqual(len(response.data["inlines"]["added"]), 3)
        self.assertEqual(response.data["inlines"]
                         ["added"][0]["title"], "The freedom model")

    def test_inline_bulk_updates(self):
        url = reverse('api_admin:%s_%s_change' %
                      self.author_info, kwargs={'object_id': self.a1.pk})
        data = {
            "data": {
                "name": "René Descartes",
                "age": 60,
                "user": self.user.pk,
                "is_vip": True,
                'publisher': [1]
            },
            "inlines": {
                "test_django_api_admin/book": {
                    "change": {
                        "ca4tq": {
                            "pk": self.a1_b1.pk,
                            "title": "The book of nine secrets",
                            "credits": [self.a2.pk]
                        },
                        "$fqf?": {
                            "pk": self.a1_b2.pk,
                            "title": "purple thunder lightning technique",
                            "credits": [self.a2.pk]
                        }
                    },
                    "delete": {
                        "$e&xg":  self.a1_b3.pk
                    }
                },
            },
        }
        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('inlines'))
        self.assertEqual(len(response.data["inlines"]["changed"]), 2)
        self.assertEqual(
            response.data["inlines"]["changed"][0]['title'], "The book of nine secrets")
        self.assertEqual(len(response.data["inlines"]["deleted"]), 1)
        self.assertEqual(response.data["inlines"]
                         ["deleted"][0]['title'], "Pro git")

    def test_updating_unrelated_inlines(self):
        url = reverse('api_admin:%s_%s_add' % self.author_info)
        data = {
            "data": {
                "name": "Nine Serenities Sovereign",
                "age": 60,
                "user": self.user.pk,
                "is_vip": True,
                'publisher': [1]
            },
            "inlines": {
                "test_django_api_admin/technique": {
                    "add": {
                        "2cad3": {"name": "heavenly demon transformation art"}
                    }
                }
            }
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response.data.get("errors"))
        self.assertTrue(isinstance(
            response.data["errors"]["test_django_api_admin/technique"]["non_field_errors"], list))

    def test_invalid_inline_data(self):
        url = reverse('api_admin:%s_%s_add' % self.author_info)
        data = {
            "data": {
                "name": "Nine Serenities Sovereign",
                "age": 60,
                "user": self.user.pk,
                "is_vip": True,
                'publisher': [1],
            },
            "inlines": {
                "test_django_api_admin/book": {
                    "add": {
                        "40fjq": {
                            # missing title
                            "credits": [self.a2.pk]
                        }
                    },
                    "change": {
                        "52dax": {
                            # missing pk
                            "title": "the book of nine secrets",
                            "credits": [self.a2.pk]
                        }
                    }
                },
            }
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(isinstance(
            response.data["errors"]["test_django_api_admin/book"]["40fjq"]["title"], list))
        self.assertEqual(len(Author.objects.filter(
            name="Nine Serenities Sovereign")), 0)

    def test_changing_unrelated_instance(self):
        url = reverse('api_admin:%s_%s_change' %
                      self.author_info, kwargs={'object_id': self.a1.pk})
        data = {
            "data": {
                "name": "Nine Serenities Sovereign",
                "age": 60,
                "user": self.user.pk,
                "is_vip": True,
                'publisher': [1]
            },
            "inlines": {
                "test_django_api_admin/book": {
                    "change": {
                        "abcsd": {
                            "pk": self.a2_b1.pk,
                            "title": "The book of nine secrets",
                            "credits": [self.a1.pk]
                        },
                    },
                },
            },
        }
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(isinstance(
            response.data["errors"]["test_django_api_admin/book"]["abcsd"]["pk"], list))
