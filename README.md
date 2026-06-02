<a id="readme-top"></a>



<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/demon-bixia/django-api-admin">
    <img src="assets/images/logo.png" alt="Logo" width="300" height="300">
  </a>

  <h1 align="center">Django API Admin</h1>

  <p align="center">
    A RESTful API implementation of django.contrib.admin, designed for writing custom frontends.
    <br />
    <!-- <a href="https://github.com/othneildrew/Best-README-Template"><strong>Explore the docs »</strong></a> -->
    <!-- <br /> -->
    <!-- <br /> -->
    <!-- <a href="https://github.com/othneildrew/Best-README-Template">View Demo</a>
    &middot; -->
    <a href="https://github.com/demon-bixia/django-api-admin/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/demon-bixia/django-api-admin/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#cors">CORS Configuration</a></li>
        <li><a href="#authentication">Authentication</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://github.com/demon-bixia/django-api-admin)

Django API Admin is a RESTful API implementation of the `django.contrib.admin` application, designed to make it easy to create custom frontends. This project aims to provide developers with a flexible API that mirrors the functionality of Django's built-in admin interface, allowing for seamless integration with modern web client interfaces.

### Key Features:
- **RESTful API**: Offers a comprehensive API for managing Django models, enabling developers to build custom administrative interfaces.
- **Custom Frontends**: Designed to support the development of tailored frontends that meet specific project requirements.
- **Extensible and Modular**: Build with the same `django.contrib.admin` API, allowing for easy customization and integration with existing Django projects.

The project is continuously evolving, with new features and improvements being added regularly. Contributions from the community are highly encouraged to help expand and enhance the capabilities of this tool.

To get started, follow the installation and usage instructions provided in this README. Whether you're building a new project or integrating with an existing one, Django API Admin offers the flexibility and power you need to manage your application's data effectively.



<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

This section should list any major frameworks/libraries used to bootstrap your project. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.

* [![Django][Django]][Django-url]
* [![DRF][Django REST framework]][DRF-url]
* [![DRFSPD][DRF Spectacular]][DRFSPD-url]


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

To set up the project locally, follow these steps:

### Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.12+**: Make sure Python is installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

- **Django REST framework**
  ```sh
  pip install djangorestframework
  ```
- **drf-spectacular**
  ```sh
  pip install drf-spectacular
  ```


### Installation

This section will walk you through the steps to install `django-api-admin` in your Django project. Follow these instructions to get started.

1. **Install the Package**
   ```sh
   pip install django-api-admin
   ```
2. **Add to Installed Apps** Add django_api_admin and it's requirements to the INSTALLED_APPS list in your Django project's settings.py file (the order doesn't matter):
   ```py
   # settings.py
   INSTALLED_APPS = [
      'corsheaders',
      'drf_spectacular',
      'rest_framework',
      'django_api_admin'
   ]
   ```
3. In your Django settings file, add or update the `REST_FRAMEWORK` dictionary to include the drf spectacular as the DEFAULT_SCHEMA_CLASS:  
   ```py
   # settings.py
   REST_FRAMEWORK = {
       'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
   }
   ```
4. **Add the modify_schema hook** to improve the auto generated openAPI schema  
   ```py
   # settings.py
   SPECTACULAR_SETTINGS = {
       "POSTPROCESSING_HOOKS": [
           'drf_spectacular.hooks.postprocess_schema_enums',
           'django_api_admin.hooks.modify_schema'
       ]
   }
   ```

Thats it you are now ready to register your models and implement your django admin frontend!

### CORS Configuration

If you plan to build a custom frontend in React.js or Vue.js then you might want to consider adding CORS configuration to your Django project. This will allow your frontend to make requests to your Django backend.

1. Install **django-cors-headers** package
  ```sh
  pip install django-cors-headers
  ```

2. Add `corsheaders` to `INSTALLED_APPS` in your Django project's settings.py file (the order doesn't matter):
   ```py
   # settings.py
   INSTALLED_APPS = [
      'corsheaders',
      # ...
   ]
   ```

3. Add the urls of your client side applications to the `CORS_ORIGIN_WHITELIST`
   ```py
   # settings.py
   CORS_ORIGIN_WHITELIST = (
       'http://localhost',  # jest-dom test server
       'http://localhost:3000',  # react development server
   )
   CORS_ALLOW_CREDENTIALS = True
   ```

Your client side application should now be able to make requests to your django backend!

### Authentication

Unlike `django.contrib.admin` this package doesn't include it's own authentication functionality. You will need implement authentication on your own, however the `django-api-admin` makes it very easy to add support for authentication frameworks that support `rest_framework`. This is how you can add `django-allauth` for instance:

1. Install `django-allauth`
   
```sh
pip install django-allauth
```

2. Configure `django-allauth` settings for your project

```py
# settings.py

INSTALLED_APPS = [
    # ...
    'allauth',
]

MIDDLEWARE = [
    # ...
    'allauth.account.middleware.AccountMiddleware',
    # ...
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

3. Add the `authentication_classes` to an `APIAdminSite` subclass.

```py
from django_api_admin import APIAdminSite

class AdminSite(APIAdminSite):
    def get_authentication_classes(self):
        from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication

        return [XSessionTokenAuthentication, authentication.SessionAuthentication]

site = AdminSite()
```


4. include the `django-allauth` headless urls in your `urls.py` file.

```python
# urls.py
urlpatterns = [
    # ...
    path("_allauth/", include("allauth.headless.urls")),
]
```

Now, `django-api-admin` will use the provided `authentication_classes` for authenticating users.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

This section provides a simple example on how to use django-api-admin. If you're setting up for the first time, follow the example below to get started.

1. **Create some models**
   ```py
   # models.py
   from django.db import models
 
   class Author(models.Model):
       name = models.CharField(max_length=100)
 
       def __str__(self):
           return self.name
 
   class Book(models.Model):
       title = models.CharField(max_length=100)
       author = models.ForeignKey(Author, on_delete=models.CASCADE)
 
       def __str__(self):
           return self.title
   ```
2. **Register them using the admin site**
   ```py
   # admin.py
   from django_api_admin.sites import site
   from .models import Author, Book

   site.register(Author)
   site.register(Book)
   ```
3. **Include URLs** Include the django-api-admin URLs in your  
   ```py
   # urls.py
   from django.urls import path
   from django_api_admin.sites import site

   # the admin site needs to know the name of the url prefix in this case "admin/"
   # the default is just the admin site's name which is "admin" + "/" 
   # for the default admin site
   urlpatterns = [
      path('admin/', site.urls),
   ]
   ```


<!-- _For more examples, please refer to the [Documentation](https://example.com)_ -->

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Rewrite django.contrib.admin as an API
- [x] Add support for Bulk Actions
- [x] Add OpenAPI documentation
- [ ] Add support for charts
- [ ] Add support for global full-text search

See the [open issues](https://github.com/demon-bixia/django-api-admin/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top Contributors

<a href="https://github.com/demon-bixia/django-api-admin/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=demon-bixia/django-api-admin" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See the `LICENSE` file  for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Muhammad Salah - [@daemobixia](https://t.me/demonbixia) - [msbizzaccount@gmail.com](mailto:[EMAIL_ADDRESS])

Project Link: [https://github.com/demon-bixia/django-api-admin](https://github.com/daemon-bixia/django-api-admin)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

This section is dedicated to recognizing the valuable resources and contributions that have supported this project. Below are some of the key references and inspirations that have been instrumental in the project's development journey.

* [Django Web Framework](https://www.djangoproject.com/)
* [Django Rest Framework](https://www.django-rest-framework.org/)
* [DRF Spectacular](https://github.com/tfranzel/drf-spectacular)
* [Best README Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/demon-bixia/django-api-admin.svg?style=for-the-badge
[contributors-url]: https://github.com/demon-bixia/django-api-admin/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/demon-bixia/django-api-admin.svg?style=for-the-badge
[forks-url]: https://github.com/demon-bixia/django-api-admin/network/members

[stars-shield]: https://img.shields.io/github/stars/demon-bixia/django-api-admin.svg?style=for-the-badge
[stars-url]: https://github.com/demon-bixia/django-api-admin/stargazers

[issues-shield]: https://img.shields.io/github/issues/demon-bixia/django-api-admin?style=for-the-badge
[issues-url]: https://github.com/demon-bixia/django-api-admin/issues

[license-shield]: https://img.shields.io/badge/license-MIT-blue?style=for-the-badge
[license-url]: https://github.com/demon-bixia/django-api-admin/blob/main/LICENSE

[linkedin-shield]: https://img.shields.io/badge/%40-Linkedin-blue?style=for-the-badge
[linkedin-url]: https://www.linkedin.com/in/demon-bixia/

[Django-url]: https://djangoproject.com/
[Django]: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green

[DRF-url]: https://www.django-rest-framework.org/
[Django REST framework]: https://img.shields.io/badge/django--rest--framework-3.12.4-green?style=for-the-badge&labelColor=333333&logo=django&logoColor=white&color=green

[DRFSPD-url]: https://drf-spectacular.readthedocs.io/en/latest/
[DRF Spectacular]: https://img.shields.io/badge/drf-spectacular-orange?style=for-the-badge&labelColor=333333&logo=django&logoColor=white&color=green

[product-screenshot]: assets/images/screenshot.png
