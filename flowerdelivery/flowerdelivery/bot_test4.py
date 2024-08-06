import requests
import json

# Получите CSRF токен
csrf_response = requests.get('http://127.0.0.1:8000/orders/get_csrf_token/')
csrf_token = csrf_response.json().get('csrftoken')
print("CSRF token :", csrf_token)


# Данные для создания заказа
# Данные для создания заказа
data = {
    'user': 3,  # Используйте действительный ID пользователя
    'delivery_date': '2024-07-31',
    'delivery_time': '14:00:00',
    'address': 'адрес',
    'contact': 'Контакт не указан',
    'total_amount': '9000.00',
    'status': 'Ordered',
    'items': [
        {'product': 1, 'quantity': 2, 'price': 1000.00},
        {'product': 2, 'quantity': 1, 'price': 7000.00}
    ]
}




# Преобразуем словарь в форматированную строку JSON
data_str = json.dumps(data, ensure_ascii=False, indent=4)

# Выводим строку на экран
print(data_str)

# Отправка POST запроса
#response = requests.post(
#    'http://127.0.0.1:8000/orders/api/orders/',
#    data=json.dumps(data),
#    headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf_token}
#)

#response = requests.post(
#    'http://127.0.0.1:8000/orders/api/orders/',
#    data=json.dumps(data),
#    headers={'Content-Type': 'application/json'}
#)


#print(response.status_code)
#print(response.json())
