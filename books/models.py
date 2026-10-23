from django.core.validators import MinValueValidator
from django.db import models

from books.validators import normalize_isbn, validate_isbn
from categories.models import Category


class Book(models.Model):
    title = models.CharField(max_length=250)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=17, unique=True, validators=[validate_isbn])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="books")
    stock = models.PositiveIntegerField(default=0)
    cover_image = models.ImageField(upload_to="books/covers/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        self.isbn = normalize_isbn(self.isbn)

    def save(self, *args, **kwargs):
        self.isbn = normalize_isbn(self.isbn)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("books:detail", kwargs={"pk": self.pk})
