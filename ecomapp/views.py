from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import View, TemplateView, CreateView, FormView, DetailView
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from coinbase_commerce.client import Client

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
        # context["title"] = "Home"
        allproducts = Product.objects.all().order_by("-id")

        paginator = Paginator(allproducts, 8)
        page_number = self.request.GET.get("page")
        product_list = paginator.get_page(page_number)
        # print(product_list)
        # print(page_number)
        # context["allcategories"] = Category.objects.all()
        context["product_list"] = product_list

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
            # print("user is authenticated")
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
            pm = form.cleaned_data.get("payment_method")
            print("Payment method is " + str(pm))
            print("line no 222")
            order = form.save()
            print(order.id, "order id")
            if pm == "CrytoCurrency":
                return redirect(
                    reverse("ecomapp:cryptopayment") + "?o_id=" + str(order.id)
                )
        else:
            return redirect("ecomapp:home")
        return super().form_valid(form)


class CryptoPaymentView(View):
    def get(self, request, *args, **kwargs):
        client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)
        o_id = self.request.GET.get("o_id")
        print(o_id)
        order = Order.objects.get(id=o_id)
        domain_url = "http://localhost:8000/"
        product = {
            "name": "Order_" + str(order.id),
            "local_price": {"amount": order.total, "currency": "USD"},
            "pricing_type": "fixed_price",
            "redirect_url": domain_url,
            "cancel_url": domain_url + "checkout/",
        }
        charge = client.charge.create(**product)

        return render(
            request,
            "cryptopayment.html",
            {
                "charge": charge,
            },
        )


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


class CustomerOrderDetailView(DetailView):
    template_name = "customerorderdetail.html"
    model = Order
    context_object_name = "ord_obj"

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated and request.user.customer:
            print("user is authenticated")
            order_id = self.kwargs["pk"]
            try:
                order = Order.objects.get(id=order_id)
                if request.user.customer != order.cart.customer:
                    return redirect("ecomapp:customerprofile")
            except:
                return redirect("ecomapp:customerprofile")

        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)


class CustomerProfileView(TemplateView):
    template_name = "customerprofile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context["customer"] = customer
        orders = Order.objects.filter(cart__customer=customer).order_by("-id")
        context["orders"] = orders
        return context

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated and request.user.customer:
            # print("user is authenticated")
            pass
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)


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


class SearchView(TemplateView):
    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kw = self.request.GET.get("keyword")
        results = Product.objects.filter(
            Q(title__icontains=kw)
            | Q(discription__icontains=kw)
            | Q(return_policy__icontains=kw)
        )
        # print(results)
        # print(kw)
        context["results"] = results
        return context
