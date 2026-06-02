import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from allauth.account.models import EmailAddress

from example.factories import ProductFactory, ReviewFactory, CustomerFactory, CategoryFactory, TrademarkFactory, AdminUserFactory
from example.models import Product, Review, Category, Trademark, Customer

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with sample data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning database...")
        EmailAddress.objects.all().delete()
        Review.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Trademark.objects.all().delete()
        Customer.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write("Creating default superuser...")
        # Since we clean the database, we can just create the admin
        AdminUserFactory.create(
            username="admin", 
            email="admin@email.com", 
            is_superuser=True
        )

        self.stdout.write("Creating staff users...")
        AdminUserFactory.create_batch(5, is_superuser=False)

        self.stdout.write("Creating categories and trademarks...")
        categories = CategoryFactory.create_batch(10)
        trademarks = TrademarkFactory.create_batch(10)

        self.stdout.write("Creating customers...")
        customers = CustomerFactory.create_batch(100)

        self.stdout.write("Creating 1000 products and 10 reviews for each...")

        for i in range(1, 1001):
            product = ProductFactory.create(
                category=random.choice(categories),
                trademark=random.choice(trademarks)
            )

            # Create 10 reviews for this product
            for _ in range(10):
                ReviewFactory.create(
                    product=product,
                    customer=random.choice(customers)
                )

            if i % 10 == 0:
                self.stdout.write(f"Processed {i} products...")

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {Product.objects.count()} products and {Review.objects.count()} reviews."))
