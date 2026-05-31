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

from django.urls import path
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, URLPatternsTestCase, APIRequestFactory

from django_api_admin import APIModelAdmin

from .admin import site

UserModel = get_user_model()


class AdminTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api_admin/", site.urls),
    ]

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

        # Create a superuser
        self.user = UserModel.objects.create_superuser(username="admin")
        self.user.set_password("password")
        self.user.save()

        # Authenticate the superuser
        self.client.force_authenticate(user=self.user)

    def test_registering_models(self):
        from django.db import models

        class Meta:
            app_label = "django_api_admin"

        # dynamically some create models and modelAdmins
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
