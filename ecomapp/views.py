from multiprocessing import context
from django.shortcuts import render
from django.views.generic import TemplateView
from .models import *

# Create your views here.


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        context["allproducts"] = Product.objects.all().order_by("-id")
        context["allcategories"] = Category.objects.all()
        return context


class AboutView(TemplateView):
    template_name = "about.html"


class ContactView(TemplateView):
    template_name = "contact.html"


class AllProductView(TemplateView):
    template_name = "allproduct.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allcategories"] = Category.objects.all()
        return context


class ProductDetailView(TemplateView):
    template_name = "productdetail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs["slug"]
        product = Product.objects.get(slug=slug)
        product.view_count += 1
        product.save()
        context["product"] = product
        return context


class AddToCartView(TemplateView):
    template_name = "addtocat.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # getting product id
        product_id = self.kwargs["pro_id"]
        # print(product_id, "888888888")
        # getting product
        product_obj = Product.objects.get(id=product_id)
        cart_id = self.request.session.get("cart_id", None)

        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            # print("old cart")
            this_product_in_cart = cart_obj.cartproduct_set.filter(product=product_obj)
            if this_product_in_cart.exists():  # if product already in cart
                cartproduct = this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
            else:  # item does not exist in cart
                cartproduct = CartProduct.objects.create(
                    cart=cart_obj,
                    product=product_obj,
                    quantity=1,
                    rate=product_obj.selling_price,
                    subtotal=product_obj.selling_price,
                )
                cart_obj.total += product_obj.selling_price
                cart_obj.save()

        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session["cart_id"] = cart_obj.id
            # print("new cart cart")
            cartproduct = CartProduct.objects.create(
                cart=cart_obj,
                product=product_obj,
                quantity=1,
                rate=product_obj.selling_price,
                subtotal=product_obj.selling_price,
                total=product_obj.selling_price,
            )
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
        return context


class MyCartView(TemplateView):
    template_name = "mycart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context["cart"] = cart
        return context