from django.db import models
from django.utils import timezone
from decimal import Decimal

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name="orders")
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def calculate_total(self):
        total = sum(p.price for p in self.products.all())
        self.total_amount = total
        return self.total_amount

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total = sum(p.price for p in self.products.all())
        if self.total_amount != total:
            self.total_amount = total
            super().save(update_fields=["total_amount"])
