from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("records:category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    stock = models.PositiveIntegerField(default=0)
    brand = models.CharField(max_length=100, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("records:product_detail", kwargs={"slug": self.slug})

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        db_index=True,
    )
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.product.name}"