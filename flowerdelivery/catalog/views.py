from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
from django.views.generic import ListView
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'


class HomePageView(TemplateView):
    template_name = 'catalog/home.html'
    context_object_name = 'home'

#def home(request):
#    return render(request, 'catalog/home.html')
