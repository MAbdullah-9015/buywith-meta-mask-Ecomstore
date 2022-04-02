from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["order_by", "shipping_address", "mobile", "email"]
