# Book Management

A Django book catalogue with MySQL configuration, user accounts, book management, and starter category/cart/order/dashboard apps.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Create a MySQL database (default name: `book_management`) using `utf8mb4`, and create a MySQL user with access to it.
4. Copy `.env.example` to `.env` and enter your MySQL credentials in `.env`. The `.env` file is ignored by Git and should not be committed. PowerShell environment variables, if set, take precedence over `.env`.

   `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` can also be set in `.env`.

   Defaults are intended for local development only.
5. Apply migrations: `python manage.py migrate`
6. Create a staff account for book/category management: `python manage.py createsuperuser`
7. Start the server: `python manage.py runserver`

Staff users can create, edit, and delete books and categories. Anyone can browse the catalogue, search by title/author/ISBN, and filter or sort by category and price. Registered users can add books to a cart, update quantities, remove items, and place orders. Checkout rechecks and decrements stock in a database transaction; customers can review their order history and current status. Uploaded book covers are stored in `media/`.

Staff can use the Bootstrap dashboard to review catalogue/order/sales/low-stock summaries, update order statuses, and update books with low inventory. Orders can move through Pending, Confirmed, Shipped, Delivered, or Cancelled; cancelling a pending or confirmed order restores its ordered quantities to stock. The Django admin supports book and category management and read-only order inspection; order status changes are handled through the dashboard so inventory remains consistent.
