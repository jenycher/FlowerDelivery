# orders/views.py

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Order, CartItem
from django.conf import settings
from catalog.models import Product
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from django.views.generic import CreateView
from .forms import OrderForm, AddToCartForm # Предполагаем, что форма заказа находится в forms.py
from .serializers import OrderSerializer, OrderStatusSerializer, OrderListSerializer
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import user_passes_test
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accounts.models import CustomUser
import logging

logger = logging.getLogger(__name__)
@login_required
def update_cart(request):
    if request.method == 'POST':
        if 'update' in request.POST:
            for key, value in request.POST.items():
                if key.startswith('quantity_'):
                    item_id = key.split('_')[1]
                    try:
                        cart_item = CartItem.objects.get(id=item_id, user=request.user)
                        cart_item.quantity = int(value)
                        cart_item.save()
                    except CartItem.DoesNotExist:
                        continue
        elif 'remove' in request.POST:
            remove_items = request.POST.getlist('remove_items')
            CartItem.objects.filter(id__in=remove_items, user=request.user).delete()

    return redirect('cart_detail')



@login_required
def add_to_cart(request):
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            quantity = form.cleaned_data['quantity']
            product = get_object_or_404(Product, id=product_id)

            # Найдите существующий элемент корзины или создайте новый
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                # Обновите количество, если элемент корзины уже существует
                cart_item.quantity += quantity
                cart_item.save()

            return redirect('cart_detail')  # Перенаправление к деталям корзины
    return redirect('category_list')


@login_required
def cart_detail(request):
    cart_items = CartItem.objects.filter(user=request.user)
    return render(request, 'orders/cart_detail.html', {'cart_items': cart_items})

def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})



def order_create(request):
    logger.info('Старт обработки создания заказа')

    # Получаем все товары в корзине пользователя
    cart_items = CartItem.objects.filter(user=request.user)

    # Проверяем, есть ли товары в корзине
    if not cart_items.exists():
        return redirect('cart_detail')  # Перенаправляем, если корзина пуста

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Создаем новый заказ
            order = form.save(commit=False)
            order.user = request.user
            order.created_at = timezone.now()
            order.total_amount = sum(item.quantity * item.product.price for item in cart_items)
            order.save()

            # Сохраняем товары в заказе
            for item in cart_items:
                order.items.create(
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Отправляем подтверждение заказа на email
            send_mail(
                'Подтверждение заказа',
                f'Спасибо за Ваш заказ, {order.user.username}.\n\n'
                f'Your order will be delivered on {order.delivery_date} at {order.delivery_time} to {order.address}.\n'
                f'The total amount is {order.total_amount} руб.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )

            # Очищаем корзину
            cart_items.delete()
            return redirect('order_success')  # Перенаправляем на страницу успеха
    else:
        form = OrderForm()

    return render(request, 'orders/order_create.html', {'form': form, 'cart_items': cart_items})
class OrderCreateView(CreateView):
    model = Order
    form_class = AddToCartForm
    template_name = 'orders/order_form.html'
    success_url = '/orders/success/'

    def form_valid(self, form):
        # Дополнительная логика, если необходимо
        return super().form_valid(form)
def order_success(request):
    return render(request, 'orders/order_success.html')


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Если total_amount не вычисляется автоматически, то можно рассчитать его здесь
    if not order.total_amount:
        order.total_amount = sum(item.quantity * item.price for item in order.items.all())
        order.save()
    return render(request, 'orders/order_detail.html', {'order': order})

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


#@method_decorator(csrf_exempt, name='dispatch')
class OrderCreateApi(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response({"message": "Order created successfully", "id": order.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_csrf_token_view(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrftoken': csrf_token})


# Проверка на администратора
def is_admin(user):
    return user.is_staff


@user_passes_test(is_admin)
def admin_orders_view(request):
    status = request.GET.get('status', '')
    delivery_date = request.GET.get('delivery_date', '')

    orders = Order.objects.all()

    if status:
        orders = orders.filter(status=status)
    if delivery_date:
        orders = orders.filter(delivery_date=delivery_date)

    return render(request, 'orders/admin_orders.html', {'orders': orders})

@user_passes_test(is_admin)
def change_order_status(request, order_id, status):
    order = get_object_or_404(Order, id=order_id)
    order.status = status
    order.save()
    return redirect('admin_orders')

class OrderStatusApi(APIView):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderStatusSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

class UserOrdersApi(APIView):
    def get(self, request):
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            return Response({'error': 'telegram_id не указан'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(telegram_id=telegram_id)
            orders = Order.objects.filter(user=user)
            serializer = OrderListSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Пользователь с указанным telegram_id не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        except CustomUser.MultipleObjectsReturned:
            return Response({'error': 'Найдено несколько пользователей с указанным telegram_id'},
                            status=status.HTTP_400_BAD_REQUEST)
class OrderListApi(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

@login_required
def repeat_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    for item in order.items.all():
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=item.product,
            defaults={'quantity': item.quantity}
        )
        if not created:
            cart_item.quantity += item.quantity
            cart_item.save()
    return redirect('cart_detail')

