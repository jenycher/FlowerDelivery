from django.urls import path, include
from . import views, OrderViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
   # path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('success/', views.order_success, name='order_success'),
    path('create/', views.order_create, name='order_create'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('', include(router.urls)),

]




