from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from catalog.models import Product

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=255)

    def __str__(self):
        return f'Order {self.id} by {self.user}'
