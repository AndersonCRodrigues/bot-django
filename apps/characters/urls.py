from django.urls import path
from . import views

app_name = "characters"

urlpatterns = [
    path("", views.character_list, name="list"),
    path("create/", views.character_create, name="create"),
    path("<str:character_id>/", views.character_detail, name="detail"),
    path("<str:character_id>/delete/", views.character_delete, name="delete"),
]
