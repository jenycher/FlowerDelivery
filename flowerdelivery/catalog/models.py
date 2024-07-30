# catalog/models.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='Описание отсутствует')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)

    def __str__(self):
        return self.name




