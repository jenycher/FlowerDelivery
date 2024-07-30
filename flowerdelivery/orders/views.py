# orders/views.py

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import CartItem, Order
from django.conf import settings
from catalog.models import Product
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from django.views.generic import CreateView
from .forms import OrderForm, AddToCartForm # Предполагаем, что форма заказа находится в forms.py


def update_cart(request):
    if request.method == 'POST':
        # Обработка обновления корзины
        for item_id in request.POST.getlist('remove_items'):
            CartItem.objects.filter(id=item_id).delete()

        for item_id in request.POST:
            if item_id.startswith('quantity_'):
                item = CartItem.objects.get(id=item_id.split('_')[1])
                item.quantity = int(request.POST[item_id])
                item.save()

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
                'Order Confirmation',
                f'Thank you for your order, {order.user.username}.\n\n'
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
    success_url = '/orders/success/'  # Замените на ваш URL для успешного создания заказа

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

