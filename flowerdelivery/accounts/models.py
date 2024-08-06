from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Например, если добавили поле phone_number
    # phone_number = models.CharField(max_length=15, blank=True, null=True)
    telegram_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    pass

