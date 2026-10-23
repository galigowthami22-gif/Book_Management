from django.urls import path

from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("checkout/", views.checkout, name="checkout"),
]
