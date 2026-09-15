import random
import requests
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker

from records.models import Category, Product, ProductImage

fake = Faker()

CATEGORY_NAMES = [
    "Electronics", "Home & Kitchen", "Sports & Outdoors", "Books",
    "Toys & Games", "Clothing", "Beauty & Personal Care", "Automotive",
    "Office Supplies", "Pet Supplies",
]

BRANDS = [
    "Nova", "Zenith", "Orbit", "Pulse", "Vertex", "Aster",
    "Halo", "Drift", "Cobalt", "Ember",
]


class Command(BaseCommand):
    help = "Seed the database with fake categories and products for performance testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5000,
            help="Number of products to create (default: 5000)",
        )
        parser.add_argument(
            "--with-images",
            action="store_true",
            help="Download a real placeholder photo for each seeded product (slower).",
        )

    def handle(self, *args, **options):
        count = options["count"]

        categories = []
        for name in CATEGORY_NAMES:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )
            categories.append(category)

        self.stdout.write(f"Using {len(categories)} categories.")

        batch_size = 500
        products = []
        existing_count = Product.objects.count()

        for i in range(count):
            name = f"{random.choice(BRANDS)} {fake.word().capitalize()} {fake.word().capitalize()} #{existing_count + i + 1}"
            slug = slugify(name)
            products.append(Product(
                category=random.choice(categories),
                name=name,
                slug=slug,
                description=fake.paragraph(nb_sentences=3),
                price=Decimal(random.randrange(500, 50000)) / 100,
                stock=random.randint(0, 500),
                brand=random.choice(BRANDS),
                is_active=random.random() > 0.1,
            ))

            if len(products) >= batch_size:
                created = Product.objects.bulk_create(products, batch_size=batch_size)
                if options["with_images"]:
                    self._attach_images(created)
                self.stdout.write(f"Inserted {i + 1}/{count} products...")
                products = []

        if products:
            created = Product.objects.bulk_create(products, batch_size=batch_size)
            if options["with_images"]:
                self._attach_images(created)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Total products in database: {Product.objects.count()}"
        ))

    def _attach_images(self, products):
        for product in products:
            try:
                url = f"https://picsum.photos/seed/{product.slug}/600/600"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                image = ProductImage(product=product, is_primary=True, order=0)
                image.image.save(
                    f"{product.slug}.jpg",
                    ContentFile(response.content),
                    save=True,
                )
            except requests.RequestException:
                self.stdout.write(f"  Image download failed for {product.slug}, skipping.")