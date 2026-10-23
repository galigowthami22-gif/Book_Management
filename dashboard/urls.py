from django.urls import path

from dashboard.views import DashboardView, OrderStatusUpdateView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="index"),
    path("orders/<int:pk>/status/", OrderStatusUpdateView.as_view(), name="order-status"),
]
