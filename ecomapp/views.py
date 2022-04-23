from aiohttp import request
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, CreateView, FormView
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login, logout

# Create your views here.


class Ecommixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and request.user.customer:
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)


class HomeView(Ecommixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        context["allproducts"] = Product.objects.all().order_by("-id")
        context["allcategories"] = Category.objects.all()
        return context


class AboutView(Ecommixin, TemplateView):
    template_name = "about.html"


class ContactView(Ecommixin, TemplateView):
    template_name = "contact.html"


class AllProductView(Ecommixin, TemplateView):
    template_name = "allproduct.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allcategories"] = Category.objects.all()
        return context


class ProductDetailView(Ecommixin, TemplateView):
    template_name = "productdetail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs["slug"]
        product = Product.objects.get(slug=slug)
        product.view_count += 1
        product.save()
        context["product"] = product
        return context


class AddToCartView(Ecommixin, TemplateView):
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
            )
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
        return context


class MyCartView(Ecommixin, TemplateView):
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


class ManageCartView(Ecommixin, View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs["cp_id"]
        action = request.GET.get("action")
        print(action, cp_id)
        print("this ius manage cart sectiion")
        cp_obj = CartProduct.objects.get(id=cp_id)
        cart_obj = cp_obj.cart
        # cart_id = request.session.get("cart_id", None)
        #    if cart_obj:
        #          cart2 = Cart.objects.get(id=cart_id)
        #           if cart1 != cart2:
        #                return redirect("ecomapp:mycart")
        if action == "inc":
            cp_obj.quantity += 1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
        elif action == "dcr":
            cp_obj.quantity -= 1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity == 0:
                cp_obj.delete()
        elif action == "rmv":
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        else:
            pass

        return redirect("ecomapp:mycart")


class EmptyCartView(Ecommixin, View):
    def get(self, requesr, *args, **kwargs):
        cart_id = self.request.session.get("cart_id", None)
        print(cart_id, "cart_id")
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total = 0
            cart.save()
        return redirect("ecomapp:mycart")


class CheckoutView(Ecommixin, CreateView):
    template_name = "checkout.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("ecomapp:home")
    # Muhammad Asad
    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated and request.user.customer:
            print("user is authenticated")
            pass
        else:
            return redirect("/login/?next=/checkout/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context["cart"] = cart
        return context

    def form_valid(self, form):
        cart_id = self.request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session["cart_id"]

        else:
            return redirect("ecomapp:home")
        return super().form_valid(form)


class CustomerRegisterationView(CreateView):
    template_name = "customerregisteration.html"
    form_class = CustomerRegisterationForm
    success_url = reverse_lazy("ecomapp:home")

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")

        user = User.objects.create_user(
            username=username, password=password, email=email
        )
        form.instance.user = user
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url


class CustomerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("ecomapp:home")


class CustomerLoginView(FormView):
    template_name = "customerlogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("ecomapp:home")

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)

        else:
            return render(
                self.request,
                "customerlogin.html",
                {"form": CustomerLoginForm, "error": "Invalid Credentials"},
            )
        return super().form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url
