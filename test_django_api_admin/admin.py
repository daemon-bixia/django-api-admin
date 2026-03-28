"""
Test admins are used in tests.py to test django_api_admin.
not included in the production branch
"""

from django.urls import path
from django.db import models
from django.contrib import admin
from django.utils import timezone

from test_django_api_admin import views as custom_api_views
from test_django_api_admin.models import Author, Publisher, Book, GuestEntry
from test_django_api_admin.actions import make_old, make_young
from test_django_api_admin.serializers import AuthorSerializer

from django_api_admin.sites import APIAdminSite
from django_api_admin.admins.inline_admin import TabularInlineAPI
from django_api_admin.admins.model_admin import APIModelAdmin
from django_api_admin.decorators import register, display


class CustomAPIAdminSite(APIAdminSite):
    def hello_world_view(self, request):
        return custom_api_views.HelloWorldView.as_view()(request)

    def get_urls(self):
        urlpatterns = super(CustomAPIAdminSite, self).get_urls()
        urlpatterns.append(
            path('hello_world/', self.hello_world_view, name='hello'))
        return urlpatterns

    def get_authentication_classes(self):
        from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication
        from rest_framework import authentication

        return [XSessionTokenAuthentication, authentication.SessionAuthentication]

    def has_permission(self, request):
        from allauth.mfa.models import Authenticator

        if not request.user.is_authenticated:
            return False

        joined_ms = int(request.user.date_joined.timestamp() * 1000)
        now_ms = int(timezone.now().timestamp() * 1000)

        if now_ms - joined_ms < 3 * 24 * 60 * 60 * 1000:
            has_mfa = True
        else:
            has_mfa = Authenticator.objects.filter(user=request.user).exists()

        return request.user.is_active and request.user.is_staff and has_mfa


site = CustomAPIAdminSite(name='api_admin', include_auth=True)


class APIBookInline(TabularInlineAPI):
    model = Book


@register(Publisher, site=site)
class PublisherAPIAdmin(APIModelAdmin):
    search_fields = ('name',)


# register in api_admin_site
@register(Author, site=site)
class AuthorAPIAdmin(APIModelAdmin):
    serializer_class = AuthorSerializer

    list_display = ('name', 'age', 'user', 'is_old_enough',
                    'title', 'gender', 'date_joined',)
    list_display_links = ('name',)
    list_filter = ('is_vip', 'age')
    list_editable = ('age',)
    list_per_page = 6
    empty_value_display = '-'
    search_fields = ('name', 'publisher__name',)
    ordering = ('-age',)

    # filter_horizontal = ('publisher')
    raw_id_fields = ('publisher', )
    autocomplete_fields = ('publisher',)
    date_hierarchy = 'date_joined'

    serializerfield_overrides = {
        models.CharField: {'help_text': 'This is a custom help text for all CharFields'},
    }

    actions = (make_old, make_young,)
    actions_selection_counter = True

    fieldsets = (
        ('Information', {
            'fields': (('name', 'age'), 'is_vip', 'user', 'publisher', 'is_old_enough', 'date_joined', 'location')}),
    )
    # a list of field names to exclude from the add/change form.
    exclude = ('gender',)
    readonly_fields = ('date_joined', 'is_old_enough')

    inlines = [APIBookInline, ]

    @display(description='is this author old enough')
    def is_old_enough(self, obj, context=None):
        return obj.age > 10


site.register(Book)

# register in default admin site


class BookInline(admin.TabularInline):
    model = Book
    filter_horizontal = ('credits',)


class PublisherAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'user', 'is_old_enough',
                    'title', 'gender', 'date_joined')
    list_display_links = ('name',)
    list_filter = ('is_vip', 'age')
    list_editable = ('title',)
    list_per_page = 6
    empty_value_display = '-'
    search_fields = ('name', 'publisher__name',)
    ordering = ('-age',)

    # filter_horizontal = ('publisher')
    raw_id_fields = ('publisher', )
    autocomplete_fields = ('publisher',)
    date_hierarchy = 'date_joined'

    formfield_overrides = {
        models.CharField: {'help_text': 'This is a custom help text for all CharFields'},
    }

    actions = (make_old, make_young,)
    actions_selection_counter = True

    fieldsets = (
        ('Information', {
         'fields': (('name', 'age'), 'is_vip', 'user', 'publisher', 'is_old_enough', 'date_joined',)}),
    )
    # a list of field names to exclude from the add/change form.
    exclude = ('gender',)
    readonly_fields = ('date_joined', 'is_old_enough',)

    inlines = [BookInline]

    @admin.display(description='is this author a vip')
    def is_a_vip(self, obj):
        return obj.is_vip

    @admin.display(description='is this author old enough')
    def is_old_enough(self, obj):
        return obj.age > 10


admin.site.register(Author, AuthorAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(GuestEntry)
