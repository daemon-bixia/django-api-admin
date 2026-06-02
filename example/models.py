from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True,
                            help_text="Unique slug for the category.")
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL,
                               null=True, blank=True, related_name="subcategories")
    image = models.ImageField(
        upload_to="category_images/", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Trademark(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_status = models.CharField(max_length=50, choices=[
        ("in_stock", "In Stock"),
        ("out_of_stock", "Out of Stock"),
        ("pre_order", "Pre-order"),
    ])
    trademark = models.ForeignKey(
        Trademark, on_delete=models.PROTECT, related_name="products")
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    related_products = models.ManyToManyField("self", blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product-detail", kwargs={"pk": self.pk})


class ProductImage(models.Model):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="image")
    tags = models.ManyToManyField(Tag, blank=True, related_name="images")
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.name}"


class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer_profile_ecommerce")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="reviews")
    review_title = models.CharField(max_length=255)
    review_content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)])

    def __str__(self):
        return f"{self.review_title} - {self.rating}"


class Metadata(models.Model):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="meta_data")
    metadata = models.JSONField(
        default=dict, help_text="Stores metadata in a key-value format.")

    def __str__(self):
        return f"Metadata for {self.product.name}"


class ProductFeature(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="features_list")
    features = models.JSONField(
        default=list, help_text="JSON list of product features.")

    def __str__(self):
        return f"Features for {self.product.name}"


class Catalog(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="catalogs")
    catalog_file = models.FileField(upload_to="catalogs/")

    def __str__(self):
        return f"Catalog for {self.product.name}"


class Order(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders")
    products = models.ManyToManyField(Product, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="pending")

    def __str__(self):
        return f"Order {self.id} by {self.customer.user.username}"
