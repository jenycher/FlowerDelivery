# Generated by Django 5.1rc1 on 2024-08-06 19:54

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_alter_order_delivery_date_alter_order_delivery_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery_date',
            field=models.DateField(default=datetime.datetime(2024, 8, 6, 19, 54, 32, 617136, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_time',
            field=models.TimeField(default=datetime.datetime(2024, 8, 6, 19, 54, 32, 617136, tzinfo=datetime.timezone.utc)),
        ),
    ]
