#import requests
#category_id = 1
#response = requests.get(f'http://127.0.0.1:8000/api/products/', params={'category': 1})

#print(response.status_code)
#print(response.json())

#curl -X GET "http://127.0.0.1:8000/api/category/?category=1" -H  "accept: application/json"

import requests
import asyncio

import settings
from orders.models import Order

def get_order_ids():
    orders = Order.objects.all()
    order_ids = [order.id for order in orders]
    return order_ids

order_ids = get_order_ids()
print(order_ids)