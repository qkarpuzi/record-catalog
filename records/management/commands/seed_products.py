import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker

from records.models import Category, Product

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

    def handle(self, *args, **options):
        count = options["count"]

        # Create categories first (small, fixed list — safe to get_or_create individually)
        categories = []
        for name in CATEGORY_NAMES:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )
            categories.append(category)

        self.stdout.write(f"Using {len(categories)} categories.")

        # Build products in memory, then bulk_create in batches
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
                Product.objects.bulk_create(products, batch_size=batch_size)
                self.stdout.write(f"Inserted {i + 1}/{count} products...")
                products = []

        if products:
            Product.objects.bulk_create(products, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Total products in database: {Product.objects.count()}"
        ))