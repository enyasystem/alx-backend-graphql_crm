import re
import graphene
from graphene import Field, List, String, ID
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from datetime import datetime

PHONE_REGEX = re.compile(r'^(\+\d{1,15}|\d{1,4}[-\s]\d{3}[-\s]\d{3,4})$')

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        filterset_class = CustomerFilter

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        filterset_class = ProductFilter

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        filterset_class = OrderFilter

# Query
class Query(graphene.ObjectType):
    hello = graphene.String()
    all_customers = DjangoFilterConnectionField(CustomerType)
    all_products = DjangoFilterConnectionField(ProductType)
    all_orders = DjangoFilterConnectionField(OrderType)

    def resolve_hello(root, info):
        return "Hello, GraphQL!"

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = Field(CustomerType)
    message = String()
    errors = List(String)

    @staticmethod
    def mutate(root, info, name, email, phone=None):
        errors = []
        if Customer.objects.filter(email=email).exists():
            errors.append("Email already exists")
            return CreateCustomer(customer=None, message="Failed", errors=errors)
        if phone and not PHONE_REGEX.match(phone):
            errors.append("Invalid phone format")
            return CreateCustomer(customer=None, message="Failed", errors=errors)
        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created", errors=None)

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = List(CustomerType)
    errors = List(String)

    @staticmethod
    def mutate(root, info, input):
        created = []
        errors = []
        with transaction.atomic():
            for idx, c in enumerate(input):
                name = c.name
                email = c.email
                phone = c.phone
                if Customer.objects.filter(email=email).exists():
                    errors.append(f"Record {idx}: Email {email} already exists")
                    continue
                if phone and not PHONE_REGEX.match(phone):
                    errors.append(f"Record {idx}: Invalid phone {phone}")
                    continue
                created.append(Customer.objects.create(name=name, email=email, phone=phone))
        return BulkCreateCustomers(customers=created, errors=errors or None)

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int()

    product = Field(ProductType)
    errors = List(String)

    @staticmethod
    def mutate(root, info, name, price, stock=0):
        errors = []
        if price <= 0:
            errors.append("Price must be positive")
            return CreateProduct(product=None, errors=errors)
        if stock is None:
            stock = 0
        if stock < 0:
            errors.append("Stock cannot be negative")
            return CreateProduct(product=None, errors=errors)
        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product, errors=None)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = ID(required=True)
        product_ids = List(ID, required=True)
        order_date = graphene.types.datetime.DateTime()

    order = Field(OrderType)
    errors = List(String)

    @staticmethod
    def mutate(root, info, customer_id, product_ids, order_date=None):
        errors = []
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            errors.append("Invalid customer ID")
            return CreateOrder(order=None, errors=errors)
        if not product_ids:
            errors.append("At least one product must be selected")
            return CreateOrder(order=None, errors=errors)
        products = []
        for pid in product_ids:
            try:
                prod = Product.objects.get(pk=pid)
                products.append(prod)
            except Product.DoesNotExist:
                errors.append(f"Invalid product ID: {pid}")
        if errors:
            return CreateOrder(order=None, errors=errors)
        order = Order.objects.create(customer=customer, order_date=order_date or datetime.now())
        order.products.set(products)
        order.calculate_total()
        order.save()
        return CreateOrder(order=order, errors=None)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
