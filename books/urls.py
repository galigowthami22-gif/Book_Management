from django.urls import path

from books import views

app_name = "books"

urlpatterns = [
    path("", views.BookListView.as_view(), name="list"),
    path("add/", views.BookCreateView.as_view(), name="create"),
    path("<int:pk>/", views.BookDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.BookUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.BookDeleteView.as_view(), name="delete"),
]
