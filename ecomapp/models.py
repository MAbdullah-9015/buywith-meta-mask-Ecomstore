from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products")
    marked_price = models.PositiveBigIntegerField()
    selling_price = models.PositiveBigIntegerField()
    discription = models.TextField()
    warranty = models.CharField(max_length=200, null=True, blank=True)
    return_policy = models.CharField(max_length=200, null=True, blank=True)
    view_count = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return self.title


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    address = models.CharField(max_length=200, null=True, blank=True)
    joined_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Cart(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, null=True, blank=True
    )
    total = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Cart" + str(self.id)


class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    rate = models.PositiveBigIntegerField(default=0)
    subtotal = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return "Cart" + str(self.cart.id) + "CartProduct" + str(self.id)


ORDER_STATUS = (
    ("Order Recived", "Order Recived"),
    ("Order Processing", "Order Processing"),
    ("Order completed", "Order completed"),
    ("On the way", "On the way"),
    ("Order cancelled", "Order cancelled"),
)


class Order(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    order_by = models.CharField(max_length=200)
    shipping_address = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    subtotal = models.PositiveBigIntegerField(default=0)
    discount = models.PositiveBigIntegerField(default=0)
    total = models.PositiveBigIntegerField(default=0)
    order_status = models.CharField(max_length=200, choices=ORDER_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Order" + str(self.id)
