from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView
from .models import Order

class OrderCreateView(CreateView):
    model = Order
    fields = ['products', 'address']
    template_name = 'orders/order_form.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
