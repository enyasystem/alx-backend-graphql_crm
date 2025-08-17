#!/usr/bin/env python
import os
import django
import sys

sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

django.setup()

from crm.models import Customer, Product


def run():
    Customer.objects.all().delete()
    Product.objects.all().delete()

    customers = [
        {"name": "Alice", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob", "email": "bob@example.com", "phone": "123-456-7890"},
    ]
    for c in customers:
        Customer.objects.create(**c)

    products = [
        {"name": "Laptop", "price": 999.99, "stock": 10},
        {"name": "Mouse", "price": 19.99, "stock": 100},
    ]
    for p in products:
        Product.objects.create(**p)

    print("Seeded DB with customers and products.")


if __name__ == "__main__":
    run()
