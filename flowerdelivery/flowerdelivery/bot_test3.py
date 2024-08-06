from django.middleware.csrf import get_token
import requests
import json

def get_csrf_token():
    url = 'http://127.0.0.1:8000/orders/get_csrf_token/'  # Убедитесь, что путь правильный
    response = requests.get(url)
    print("CSRF token response:", response.json())
    return response.cookies['csrftoken']

csrf_token = get_csrf_token()


url = 'http://127.0.0.1:8000/api/orders/'
data = {
    'user': 6,  # Используйте действительный ID пользователя
    'delivery_date': '2024-08-07',
    'delivery_time': '11:00:00',
    'address': 'адрес',
    'contact': '',
    "telephone": "srt",
    'total_amount': '250.0',
    'status': 'Ordered',
    'items': [
        {'product': 3, 'quantity': 1, 'price': 250.00}
    ]
}



headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token,
    'Cookie': f'csrftoken={csrf_token}'
}

response = requests.post(url, data=json.dumps(data), headers=headers)

print(response.status_code)
try:
    print(response.json())
except json.decoder.JSONDecodeError:
    print("Response is not a valid JSON")
    print(response.text)