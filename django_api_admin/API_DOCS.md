## Introduction

**Django API Admin** is a Django package that provides a powerful, RESTful API admin interface for your Django projects. 

Key highlights include:
- **A Modern Rewrite:** It is a complete rewrite of the standard `django.contrib.admin` package, built on top of the **Django Rest Framework (DRF)**.
- **Frontend-First:** Specifically designed for developers building custom administrative front-ends using modern frameworks like **React**, **Vue**, and **Next.js**.
- **Full Feature Parity:** It provides a RESTful interface to all default `django.contrib.admin` features out of the box.
- **Extensible:** Easily customizable to add unique functionality tailored to your specific administrative needs.

## Scope

- **Core Support:** It natively supports the full suite of features found in the standard `django.contrib.admin` package.
- **Unopinionated Auth:** To remain flexible, it does **not** include or enforce any default authentication method.
- **Beyond a Mirror:** While it follows the patterns of the original admin, it is not strictly a mirror and may include enhanced features or different architectural choices that go beyond the standard Django admin.

## Authentication

Authentication is decoupled from the core package to give developers full control over their security stack.

- **Developer Responsibility:** Implementation of authentication is left entirely to the developer within their specific project.
- **Recommendation:** We highly recommend using [Django Allauth Headless](https://django-allauth.readthedocs.io/en/latest/headless.html) for a seamless, modern authentication experience that pairs perfectly with this package.
