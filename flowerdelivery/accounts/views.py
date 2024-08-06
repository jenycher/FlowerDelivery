from django.shortcuts import render
from django.http import HttpResponse
import json
import random
import string
import logging

from django.http import JsonResponse
from .models import CustomUser
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from django.urls import reverse_lazy
from django.views import generic
from .forms import CustomUserCreationForm

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User  # Замените на вашу модель пользователя
from .serializers import UserCheckSerializer


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') # После успешной регистрации перенаправляем на страницу входа
    template_name = 'accounts/signup.html'


def check_user_exists(request):
    email = request.GET.get('email')
    user = CustomUser.objects.filter(email=email).first()
    exists = user is not None
    user_id = user.id if exists else None
    return JsonResponse({'exists': exists, 'user_id': user_id})

def check_user_exists_tg(request):
    telegram_id = request.GET.get('telegram_id')
    user = CustomUser.objects.filter(telegram_id=telegram_id).first()
    exists = user is not None
    user_id = user.id if exists else None
    return JsonResponse({'exists': exists, 'user_id': user_id})

def generate_random_password(length=8):
    # Генерация случайного пароля из букв и цифр
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@csrf_exempt
def register_via_telegram(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        telegram_id = data.get('telegram_id')
        name = data.get('name')

        User = get_user_model()
        if User.objects.filter(telegram_id=telegram_id).exists():
            return JsonResponse({'error': 'Пользователь уже существует'}, status=400)

        user = User.objects.create_user(
            username=telegram_id,
            first_name=name,
            telegram_id=telegram_id,
            password=generate_random_password()
        )
        return JsonResponse({'success': 'Пользователь зарегистрирован'}, status=200)
    return JsonResponse({'error': 'Ошибка выполнения запроса регистрации пользователя'}, status=400)

class CheckUserExistsByTelegramId(APIView):
    def get(self, request, *args, **kwargs):
        telegram_id = request.GET.get('telegram_id')
        if not telegram_id:
            return Response({"error": "telegram_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            User = get_user_model()
            # Предположим, что у вас есть поле 'telegram_id' в модели User или связанной модели
            user = User.objects.filter(telegram_id=telegram_id).first()  # Замените на вашу логику поиска

            exists = user is not None
            user_id = user.id if user else None

            data = {
                "exists": exists,
                "user_id": user_id
            }
            serializer = UserCheckSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Логирование ошибки и возврат ответа с ошибкой
            logger.error(f"Ошибка проверки пользователя: {e}")
            return Response({"error": "Произошла ошибка при проверке пользователя."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

