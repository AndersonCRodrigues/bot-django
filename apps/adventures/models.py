from django.db import models
from django.contrib.auth.models import User


class Adventure(models.Model):
    GENRE_CHOICES = [
        ("fantasy", "Fantasia"),
        ("scifi", "Ficção Científica"),
        ("horror", "Terror"),
        ("mystery", "Mistério"),
        ("adventure", "Aventura"),
    ]

    DIFFICULTY_CHOICES = [
        ("easy", "Fácil"),
        ("medium", "Médio"),
        ("hard", "Difícil"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    cover_image = models.ImageField(
        upload_to="adventures/covers/", blank=True, null=True
    )
    min_players = models.IntegerField(default=1)
    max_players = models.IntegerField(default=6)
    estimated_duration = models.CharField(max_length=50)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aventura"
        verbose_name_plural = "Aventuras"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Session(models.Model):
    STATUS_CHOICES = [
        ("active", "Ativa"),
        ("paused", "Pausada"),
        ("completed", "Concluída"),
    ]

    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, related_name="sessions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    started_at = models.DateTimeField(auto_now_add=True)
    last_played = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Sessão"
        verbose_name_plural = "Sessões"
        ordering = ["-last_played"]

    def __str__(self):
        return f"{self.user.username} - {self.adventure.title}"
