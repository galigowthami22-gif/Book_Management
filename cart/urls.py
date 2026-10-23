from django.urls import path

from cart import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("add/<int:book_id>/", views.add_to_cart, name="add"),
    path("items/<int:item_id>/update/", views.update_cart_item, name="update"),
    path("items/<int:item_id>/remove/", views.remove_cart_item, name="remove"),
]
