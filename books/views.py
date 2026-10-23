from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.utils.http import urlencode
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from books.forms import BookForm
from books.mixins import StaffRequiredMixin
from books.models import Book
from categories.models import Category


class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 12

    def get_queryset(self):
        queryset = Book.objects.select_related("category")
        query = self.request.GET.get("q", "").strip()
        category_id = self.request.GET.get("category", "").strip()
        min_price = self.request.GET.get("min_price", "").strip()
        max_price = self.request.GET.get("max_price", "").strip()
        ordering = self.request.GET.get("sort", "")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(author__icontains=query)
                | Q(isbn__icontains=query)
            )
        if category_id.isdigit():
            queryset = queryset.filter(category_id=int(category_id), category__is_active=True)
        else:
            queryset = queryset.filter(category__is_active=True)
        try:
            min_value = Decimal(min_price) if min_price else None
            max_value = Decimal(max_price) if max_price else None
            maximum_price = Decimal("99999999.99")
            if (min_value is not None and (not min_value.is_finite() or min_value < 0)) or (
                max_value is not None and (not max_value.is_finite() or max_value < 0)
            ):
                raise InvalidOperation
            if (min_value is not None and min_value > maximum_price) or (
                max_value is not None and max_value > maximum_price
            ):
                raise InvalidOperation
            if min_value is not None and max_value is not None and min_value > max_value:
                raise InvalidOperation
        except InvalidOperation:
            messages.error(self.request, "Enter a valid non-negative price range.")
        else:
            if min_value is not None:
                queryset = queryset.filter(price__gte=min_value)
            if max_value is not None:
                queryset = queryset.filter(price__lte=max_value)
        if ordering in {"price", "-price", "title", "-created_at"}:
            queryset = queryset.order_by(ordering)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["selected_category"] = self.request.GET.get("category", "")
        context["min_price"] = self.request.GET.get("min_price", "")
        context["max_price"] = self.request.GET.get("max_price", "")
        context["selected_sort"] = self.request.GET.get("sort", "")
        page_query = self.request.GET.copy()
        page_query.pop("page", None)
        context["page_query"] = urlencode(page_query)
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "books/book_detail.html"
    context_object_name = "book"


class BookCreateView(StaffRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"
    success_url = reverse_lazy("books:list")

    def form_valid(self, form):
        messages.success(self.request, "Book created.")
        return super().form_valid(form)


class BookUpdateView(StaffRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "Book updated.")
        return super().form_valid(form)


class BookDeleteView(StaffRequiredMixin, DeleteView):
    model = Book
    template_name = "books/book_confirm_delete.html"
    success_url = reverse_lazy("books:list")

    def form_valid(self, form):
        messages.success(self.request, "Book deleted.")
        return super().form_valid(form)
