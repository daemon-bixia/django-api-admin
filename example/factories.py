import factory

from django.contrib.auth import get_user_model
from django.utils.text import slugify

from faker import Faker

from allauth.account.models import EmailAddress

from .models import Category, Trademark, Product, Customer, Review

User = get_user_model()

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyFunction(fake.unique.user_name)
    email = factory.LazyFunction(fake.unique.email)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "password123"
        self.set_password(password)
        if create:
            self.save()

    @factory.post_generation
    def email_address(self, create, extracted, **kwargs):
        if create:
            EmailAddress.objects.create(
                user=self,
                email=self.email,
                primary=True,
                verified=True
            )


class EmailAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailAddress

    user = factory.SubFactory(UserFactory)
    email = factory.SelfAttribute("user.email")
    primary = True
    verified = True


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.LazyFunction(fake.unique.word)
    slug = factory.LazyAttribute(lambda obj: f"{slugify(obj.name)}")
    description = factory.Faker("sentence")


class TrademarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trademark

    name = factory.Faker("company")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker("sentence", nb_words=3)
    category = factory.SubFactory(CategoryFactory)
    price = factory.Faker("pydecimal", left_digits=3,
                          right_digits=2, positive=True)
    stock_status = factory.Iterator(["in_stock", "out_of_stock", "pre_order"])
    trademark = factory.SubFactory(TrademarkFactory)
    description = factory.Faker("paragraph")


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    user = factory.SubFactory(UserFactory)
    phone_number = factory.Faker("phone_number")
    address = factory.Faker("address")
    city = factory.Faker("city")
    country = factory.Faker("country")


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    product = factory.SubFactory(ProductFactory)
    customer = factory.SubFactory(CustomerFactory)
    review_title = factory.Faker("sentence")
    review_content = factory.Faker("paragraph")
    rating = factory.Faker("random_int", min=1, max=5)
