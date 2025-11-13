from django.urls import path
from . import views

app_name = "adventures"

urlpatterns = [
    path("", views.adventure_list, name="list"),
    path("<int:pk>/", views.adventure_detail, name="detail"),
    path("<int:pk>/start/", views.adventure_start, name="start"),
    path("<int:pk>/select-character/", views.select_character, name="select_character"),
    path(
        "<int:pk>/start-with-character/",
        views.start_with_character,
        name="start_with_character",
    ),
]
