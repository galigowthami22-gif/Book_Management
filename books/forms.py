from django import forms

from books.models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = (
            "title",
            "author",
            "isbn",
            "price",
            "description",
            "category",
            "stock",
            "cover_image",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "cover_image": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "category":
                field.widget.attrs["class"] = "form-control"
        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["isbn"].help_text = "Enter a valid ISBN-10 or ISBN-13."
