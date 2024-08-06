# catalog/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Category, Product
from .serializers import ProductSerializer
from django.http import JsonResponse
import logging
from rest_framework import generics
from .serializers import ProductSerializer

def home(request):
    categories = Category.objects.all()
    return render(request, 'catalog/home.html', {'categories': categories})

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = category.products.all()
    return render(request, 'catalog/category_detail.html', {'category': category, 'products': products})

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'catalog/category_list.html', {'categories': categories})

def category_list_api(request):
    categories = Category.objects.all()
    category_data = [{'id': category.id, 'name': category.name} for category in categories]
    return JsonResponse(category_data, safe=False)

def product_list(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)

    # Фильтрация по цене
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    return render(request, 'catalog/product_list.html', {
        'category': category,
        'products': products,
        'price_min': price_min,
        'price_max': price_max,
    })


logger = logging.getLogger(__name__)

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        category_id = self.request.query_params.get('category', None)
        logger.debug(f"Category ID: {category_id}")
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
            logger.debug(f"Filtered QuerySet: {queryset}")
        return queryset




@api_view(['GET'])
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    serializer = ProductSerializer(product)
    return Response(serializer.data)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'catalog/product_detail.html', {'product': product})

def contact(request):
    return render(request, 'contact.html')




