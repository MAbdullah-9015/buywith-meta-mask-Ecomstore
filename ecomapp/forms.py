from django import forms
from .models import Customer, Order
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["order_by", "shipping_address", "mobile", "email", "payment_method"]


class CustomerRegisterationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())
    email = forms.EmailField()

    class Meta:
        model = Customer
        fields = ["username", "password", "email", "full_name", "address"]

    def clean_username(self):
        uname = self.cleaned_data.get("username")
        if User.objects.filter(username=uname).exists():
            raise forms.ValidationError("Customer with this usernaem already exists")
        return uname


class CustomerLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid credentials")
            if not user.is_active:
                raise forms.ValidationError("This user is not active")
        return self.cleaned_data
