"""
URLs para o app de jogo (game).

Rotas principais do RPG Fighting Fantasy.
"""

from django.urls import path
from apps.game import views

app_name = 'game'

urlpatterns = [
    # Lista de aventuras
    path('', views.list_adventures, name='list'),

    # Detalhes da aventura
    path('<int:pk>/', views.adventure_detail, name='detail'),

    # Iniciar jogo (AJAX POST)
    path('<int:pk>/start/', views.start_game, name='start'),

    # Interface principal de jogo
    path('play/<str:session_id>/', views.play_game, name='play'),

    # Processar ação do jogador (AJAX POST)
    path('play/<str:session_id>/action/', views.process_action, name='action'),

    # Salvar jogo (AJAX POST)
    path('play/<str:session_id>/save/', views.save_game, name='save'),

    # Deletar sessão (AJAX POST)
    path('play/<str:session_id>/delete/', views.delete_session, name='delete'),

    # Obter stats do personagem (AJAX GET)
    path('play/<str:session_id>/stats/', views.get_character_stats, name='stats'),

    # Histórico de jogadas
    path('play/<str:session_id>/history/', views.game_history, name='history'),

    # Carregar saves existentes
    path('load/', views.load_game, name='load'),
]
