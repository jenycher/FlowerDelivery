from django.middleware.csrf import get_token
import requests
import json

def my_view(request):
    csrf_token = get_token(request)
    return render(request, 'my_template.html', {'csrf_token': csrf_token})

url = 'http://127.0.0.1:8000/api/create_order/'
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
        {'product': 3, 'quantity': 1, 'price': "250.00"}
    ]
}


csrf_token = '<CSRF_TOKEN>'  # Получите токен через представление или другим способом

response = requests.post('http://127.0.0.1:8000/api/orders/', data=json.dumps(data),
                         headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf_token})

#response = requests.post(url, data=data)

print(response.status_code)
print(response.json())