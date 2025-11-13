from django.contrib import admin
from .models import Adventure, Session


@admin.register(Adventure)
class AdventureAdmin(admin.ModelAdmin):
    list_display = ["title", "genre", "difficulty", "is_published", "created_at"]
    list_filter = ["genre", "difficulty", "is_published"]
    search_fields = ["title", "description"]
    list_editable = ["is_published"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["user", "adventure", "status", "started_at", "last_played"]
    list_filter = ["status", "started_at"]
    search_fields = ["user__username", "adventure__title"]
