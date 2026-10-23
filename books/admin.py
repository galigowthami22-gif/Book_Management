from django.contrib import admin

from books.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "category", "price", "stock")
    list_filter = ("category",)
    search_fields = ("title", "author", "isbn")
