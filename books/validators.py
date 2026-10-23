import re

from django.core.exceptions import ValidationError


def normalize_isbn(value):
    return re.sub(r"[-\s]", "", value).upper()


def validate_isbn(value):
    isbn = normalize_isbn(value)
    if len(isbn) == 10 and re.fullmatch(r"\d{9}[\dX]", isbn):
        total = sum((10 - index) * (10 if char == "X" else int(char)) for index, char in enumerate(isbn))
        if total % 11 == 0:
            return
    elif len(isbn) == 13 and isbn.isdigit():
        total = sum(
            int(char) * (1 if index % 2 == 0 else 3)
            for index, char in enumerate(isbn)
        )
        if total % 10 == 0:
            return
    raise ValidationError("Enter a valid ISBN-10 or ISBN-13.", code="invalid_isbn")
