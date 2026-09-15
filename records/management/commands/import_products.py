import csv
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from records.models import Category, Product


class Command(BaseCommand):
    help = "Import products from a CSV file. Expected columns: name,category,price,stock,brand,description"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        batch_size = 500

        try:
            file = open(csv_path, newline="", encoding="utf-8")
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        reader = csv.DictReader(file)
        required_columns = {"name", "category", "price"}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            self.stderr.write(self.style.ERROR(
                f"CSV must contain at least these columns: {required_columns}. "
                f"Found: {reader.fieldnames}"
            ))
            file.close()
            return

        category_cache = {}
        products = []
        created_count = 0
        skipped_count = 0

        for line_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            category_name = (row.get("category") or "").strip()
            price_raw = (row.get("price") or "").strip()

            if not name or not category_name or not price_raw:
                self.stdout.write(f"Line {line_number}: skipped (missing name/category/price)")
                skipped_count += 1
                continue

            try:
                price = Decimal(price_raw)
            except InvalidOperation:
                self.stdout.write(f"Line {line_number}: skipped (invalid price '{price_raw}')")
                skipped_count += 1
                continue

            if category_name not in category_cache:
                category, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={"slug": slugify(category_name)},
                )
                category_cache[category_name] = category
            category = category_cache[category_name]

            stock_raw = (row.get("stock") or "0").strip()
            try:
                stock = int(stock_raw)
            except ValueError:
                stock = 0

            base_slug = slugify(name)
            slug = f"{base_slug}-{line_number}"

            products.append(Product(
                category=category,
                name=name,
                slug=slug,
                description=(row.get("description") or "").strip(),
                price=price,
                stock=stock,
                brand=(row.get("brand") or "").strip(),
                is_active=True,
            ))

            if len(products) >= batch_size:
                Product.objects.bulk_create(products, batch_size=batch_size)
                created_count += len(products)
                self.stdout.write(f"Imported {created_count} products so far...")
                products = []

        if products:
            Product.objects.bulk_create(products, batch_size=batch_size)
            created_count += len(products)

        file.close()

        self.stdout.write(self.style.SUCCESS(
            f"Import complete. Created: {created_count}, Skipped: {skipped_count}"
        ))