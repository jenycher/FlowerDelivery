# orders/models.py

from django.conf import settings
from django.db import models
from django.utils import timezone
from catalog.models import Product

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(default=timezone.now())  # Дата доставки
    delivery_time = models.TimeField(default=timezone.now())  # Время доставки
    address = models.CharField(max_length=255)  # Адрес доставки
    contact = models.CharField(max_length=255, default='Контакт не указан') # Контактная информация
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50,default="Заказан")

    def __str__(self):
        return f"Order {self.id} by {self.user}"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


    def __str__(self):
        return f"{self.quantity} x {self.product.name} for {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)