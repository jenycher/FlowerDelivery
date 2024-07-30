# orders/forms.py

from django import forms
#from catalog.models import Product
from .models import Order

class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update({'class': 'form-control'})

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address', 'contact', 'delivery_date', 'delivery_time']
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_time': forms.TimeInput(attrs={'type': 'time'}),
        }
