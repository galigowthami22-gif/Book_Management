from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import F, Sum
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from books.models import Book
from categories.models import Category
from orders.models import Order

LOW_STOCK_THRESHOLD = 5


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        low_stock_books = Book.objects.filter(stock__lte=LOW_STOCK_THRESHOLD).select_related(
            "category"
        )
        sales_statuses = (
            Order.Status.CONFIRMED,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        )
        orders = Order.objects.select_related("user").prefetch_related("items").all()
        order_page = Paginator(orders, 25).get_page(self.request.GET.get("page"))
        context.update(
            book_count=Book.objects.count(),
            category_count=Category.objects.count(),
            order_count=Order.objects.count(),
            sales_total=Order.objects.filter(status__in=sales_statuses).aggregate(
                total=Sum("total")
            )["total"]
            or Decimal("0.00"),
            low_stock_count=low_stock_books.count(),
            low_stock_threshold=LOW_STOCK_THRESHOLD,
            low_stock_books=low_stock_books[:10],
            orders=order_page.object_list,
            order_page=order_page,
            order_statuses=Order.Status.choices,
        )
        return context


class OrderStatusUpdateView(StaffRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        status = request.POST.get("status", "")
        valid_statuses = {choice for choice, _ in Order.Status.choices}
        if status not in valid_statuses:
            messages.error(request, "Select a valid order status.")
            return redirect("dashboard:index")
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=pk)
            allowed_transitions = {
                Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
                Order.Status.CONFIRMED: {Order.Status.SHIPPED, Order.Status.CANCELLED},
                Order.Status.SHIPPED: {Order.Status.DELIVERED},
                Order.Status.DELIVERED: set(),
                Order.Status.CANCELLED: set(),
            }
            if status != order.status and status not in allowed_transitions[order.status]:
                messages.error(request, "That order status transition is not allowed.")
                return redirect("dashboard:index")
            if status == Order.Status.CANCELLED and status != order.status:
                for item in order.items.select_related("book").all():
                    if item.book_id:
                        Book.objects.filter(pk=item.book_id).update(stock=F("stock") + item.quantity)
            if status != order.status:
                order.status = status
                order.save(update_fields=("status", "updated_at"))

        messages.success(request, f"Order #{order.pk} status updated.")
        return redirect("dashboard:index")
