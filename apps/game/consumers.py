"""
WebSocket Consumer para Chat em Tempo Real do RPG.

Permite comunicação bidirecional entre cliente e servidor:
- Envia ações do jogador
- Recebe narrativa em streaming
- Notificações de eventos
- Typing indicators
"""

import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from apps.game.workflows.game_workflow import process_game_action
from apps.game.models import GameSession

logger = logging.getLogger("game.websocket")


class GameConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para sessões de jogo em tempo real.

    Protocolo de mensagens:

    Cliente → Servidor:
    {
        "type": "player_action",
        "action": "Eu abro a porta",
        "session_id": "..."
    }

    Servidor → Cliente:
    {
        "type": "narrative",
        "content": "Você abre a porta...",
        "stats": {...},
        "game_over": false
    }
    """

    async def connect(self):
        """Aceita conexão WebSocket e adiciona ao grupo."""
        self.user = self.scope["user"]

        # Verificar autenticação
        if not self.user.is_authenticated:
            logger.warning("[WebSocket] Conexão rejeitada: usuário não autenticado")
            await self.close(code=4001)
            return

        # Criar room name baseado no user_id
        self.room_name = f"game_{self.user.id}"
        self.room_group_name = f"game_group_{self.user.id}"

        # Adicionar ao grupo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        logger.info(f"[WebSocket] Usuário {self.user.username} conectado")

        # Enviar mensagem de boas-vindas
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Bem-vindo, {self.user.username}!",
            "timestamp": asyncio.get_event_loop().time()
        }))

    async def disconnect(self, close_code):
        """Remove do grupo ao desconectar."""
        logger.info(f"[WebSocket] Usuário {self.user.username} desconectado (code: {close_code})")

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Recebe mensagem do cliente e processa.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            logger.debug(f"[WebSocket] Recebido: {message_type}")

            if message_type == "player_action":
                await self.handle_player_action(data)

            elif message_type == "typing":
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "typing_indicator",
                        "is_typing": data.get("is_typing", False)
                    }
                )

            elif message_type == "ping":
                await self.send(text_data=json.dumps({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                }))

            else:
                logger.warning(f"[WebSocket] Tipo de mensagem desconhecido: {message_type}")

        except json.JSONDecodeError:
            logger.error("[WebSocket] JSON inválido recebido")
            await self.send_error("Formato de mensagem inválido")

        except Exception as e:
            logger.error(f"[WebSocket] Erro ao processar mensagem: {e}", exc_info=True)
            await self.send_error(str(e))

    async def handle_player_action(self, data):
        """
        Processa ação do jogador através do workflow LangGraph.
        """
        session_id = data.get("session_id")
        player_action = data.get("action", "").strip()

        if not session_id or not player_action:
            await self.send_error("session_id e action são obrigatórios")
            return

        # Enviar acknowledgment
        await self.send(text_data=json.dumps({
            "type": "processing",
            "message": "Processando sua ação..."
        }))

        try:
            # Processar ação (pode demorar)
            result = await self.process_action_async(session_id, player_action)

            if result["success"]:
                # Enviar narrativa
                await self.send(text_data=json.dumps({
                    "type": "narrative",
                    "content": result["narrative"],
                    "stats": result["stats"],
                    "inventory": result["inventory"],
                    "current_section": result["current_section"],
                    "in_combat": result["in_combat"],
                    "game_over": result["game_over"],
                    "victory": result["victory"],
                    "turn_number": result["turn_number"]
                }))

                # Se game over, enviar evento especial
                if result["game_over"]:
                    await asyncio.sleep(1)
                    await self.send(text_data=json.dumps({
                        "type": "game_over",
                        "victory": result["victory"],
                        "message": "🎉 Vitória!" if result["victory"] else "💀 Game Over"
                    }))

            else:
                await self.send_error(result.get("error", "Erro desconhecido"))

        except Exception as e:
            logger.error(f"[WebSocket] Erro ao processar ação: {e}", exc_info=True)
            await self.send_error(f"Erro ao processar ação: {str(e)}")

    @database_sync_to_async
    def process_action_async(self, session_id: str, player_action: str):
        """Executa workflow de forma assíncrona."""
        return process_game_action(
            session_id=session_id,
            user_id=self.user.id,
            player_action=player_action
        )

    async def send_error(self, message: str):
        """Envia mensagem de erro ao cliente."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": message
        }))

    # ===== HANDLERS PARA MENSAGENS DO GRUPO =====

    async def typing_indicator(self, event):
        """Broadcast de typing indicator."""
        await self.send(text_data=json.dumps({
            "type": "typing",
            "is_typing": event["is_typing"]
        }))

    async def notification(self, event):
        """Envia notificação ao cliente."""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "title": event.get("title", "Notificação"),
            "message": event["message"],
            "level": event.get("level", "info")  # info, success, warning, error
        }))

    async def achievement_unlocked(self, event):
        """Notifica achievement desbloqueado."""
        await self.send(text_data=json.dumps({
            "type": "achievement",
            "achievement": event["achievement"],
            "message": f"🏆 Achievement desbloqueado: {event['achievement']['name']}!"
        }))
