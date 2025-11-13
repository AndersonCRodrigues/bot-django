from django.urls import path
from . import views

app_name = "game_admin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_book, name="upload_book"),
    path("books/", views.list_books, name="list_books"),
    path("books/<int:pk>/", views.book_detail, name="book_detail"),
    path("books/<int:pk>/delete/", views.delete_book, name="delete_book"),
    path("users/", views.users_list, name="users_list"),
    path("logs/", views.api_logs, name="api_logs"),
    path("health/", views.system_health, name="system_health"),
]
