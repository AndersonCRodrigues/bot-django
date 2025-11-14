"""
Sistema de Áudio para o RPG.

Gerencia música de fundo, efeitos sonoros e áudio dinâmico baseado em eventos.
"""

from enum import Enum
from typing import Dict, List, Optional


class AudioType(Enum):
    """Tipos de áudio."""
    MUSIC = "music"
    SFX = "sfx"
    AMBIENT = "ambient"
    VOICE = "voice"


class AudioEvent(Enum):
    """Eventos que acionam áudios."""
    COMBAT_START = "combat_start"
    COMBAT_HIT = "combat_hit"
    COMBAT_MISS = "combat_miss"
    COMBAT_VICTORY = "combat_victory"
    COMBAT_DEFEAT = "combat_defeat"

    ITEM_PICKUP = "item_pickup"
    ITEM_USE = "item_use"
    ITEM_DROP = "item_drop"

    DOOR_OPEN = "door_open"
    DOOR_LOCKED = "door_locked"

    TEST_SUCCESS = "test_success"
    TEST_FAILURE = "test_failure"

    LEVEL_UP = "level_up"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"

    GAME_OVER = "game_over"
    VICTORY = "victory"

    AMBIENT_DUNGEON = "ambient_dungeon"
    AMBIENT_FOREST = "ambient_forest"
    AMBIENT_TAVERN = "ambient_tavern"
    AMBIENT_CITY = "ambient_city"
    AMBIENT_CAVE = "ambient_cave"


# ===== DEFINIÇÃO DE ÁUDIOS =====

AUDIO_LIBRARY: Dict[AudioEvent, Dict] = {
    # === COMBATE ===
    AudioEvent.COMBAT_START: {
        "type": AudioType.MUSIC,
        "file": "audio/music/combat_theme.mp3",
        "volume": 0.7,
        "loop": True,
        "fade_in": 500
    },

    AudioEvent.COMBAT_HIT: {
        "type": AudioType.SFX,
        "file": "audio/sfx/sword_hit.mp3",
        "volume": 0.8,
        "loop": False
    },

    AudioEvent.COMBAT_MISS: {
        "type": AudioType.SFX,
        "file": "audio/sfx/sword_miss.mp3",
        "volume": 0.6,
        "loop": False
    },

    AudioEvent.COMBAT_VICTORY: {
        "type": AudioType.SFX,
        "file": "audio/sfx/victory.mp3",
        "volume": 0.9,
        "loop": False
    },

    AudioEvent.COMBAT_DEFEAT: {
        "type": AudioType.MUSIC,
        "file": "audio/music/game_over.mp3",
        "volume": 0.7,
        "loop": False
    },

    # === ITENS ===
    AudioEvent.ITEM_PICKUP: {
        "type": AudioType.SFX,
        "file": "audio/sfx/item_pickup.mp3",
        "volume": 0.7,
        "loop": False
    },

    AudioEvent.ITEM_USE: {
        "type": AudioType.SFX,
        "file": "audio/sfx/item_use.mp3",
        "volume": 0.8,
        "loop": False
    },

    # === INTERAÇÃO ===
    AudioEvent.DOOR_OPEN: {
        "type": AudioType.SFX,
        "file": "audio/sfx/door_open.mp3",
        "volume": 0.7,
        "loop": False
    },

    AudioEvent.DOOR_LOCKED: {
        "type": AudioType.SFX,
        "file": "audio/sfx/door_locked.mp3",
        "volume": 0.7,
        "loop": False
    },

    # === TESTES ===
    AudioEvent.TEST_SUCCESS: {
        "type": AudioType.SFX,
        "file": "audio/sfx/success.mp3",
        "volume": 0.8,
        "loop": False
    },

    AudioEvent.TEST_FAILURE: {
        "type": AudioType.SFX,
        "file": "audio/sfx/failure.mp3",
        "volume": 0.7,
        "loop": False
    },

    # === CONQUISTAS ===
    AudioEvent.ACHIEVEMENT_UNLOCK: {
        "type": AudioType.SFX,
        "file": "audio/sfx/achievement.mp3",
        "volume": 0.9,
        "loop": False
    },

    # === FIM DE JOGO ===
    AudioEvent.GAME_OVER: {
        "type": AudioType.MUSIC,
        "file": "audio/music/game_over.mp3",
        "volume": 0.7,
        "loop": False
    },

    AudioEvent.VICTORY: {
        "type": AudioType.MUSIC,
        "file": "audio/music/victory_theme.mp3",
        "volume": 0.8,
        "loop": False
    },

    # === AMBIENTE ===
    AudioEvent.AMBIENT_DUNGEON: {
        "type": AudioType.AMBIENT,
        "file": "audio/ambient/dungeon.mp3",
        "volume": 0.3,
        "loop": True
    },

    AudioEvent.AMBIENT_FOREST: {
        "type": AudioType.AMBIENT,
        "file": "audio/ambient/forest.mp3",
        "volume": 0.3,
        "loop": True
    },

    AudioEvent.AMBIENT_TAVERN: {
        "type": AudioType.AMBIENT,
        "file": "audio/ambient/tavern.mp3",
        "volume": 0.4,
        "loop": True
    },

    AudioEvent.AMBIENT_CITY: {
        "type": AudioType.AMBIENT,
        "file": "audio/ambient/city.mp3",
        "volume": 0.3,
        "loop": True
    },

    AudioEvent.AMBIENT_CAVE: {
        "type": AudioType.AMBIENT,
        "file": "audio/ambient/cave.mp3",
        "volume": 0.3,
        "loop": True
    },
}


class AudioManager:
    """
    Gerenciador de áudio do jogo.

    Responsável por:
    - Determinar quais áudios tocar baseado em eventos
    - Gerenciar transições de música
    - Controlar volume
    - Priorizar efeitos sonoros
    """

    def __init__(self):
        self.current_music: Optional[AudioEvent] = None
        self.current_ambient: Optional[AudioEvent] = None
        self.music_volume: float = 0.7
        self.sfx_volume: float = 0.8
        self.ambient_volume: float = 0.3
        self.master_volume: float = 1.0
        self.muted: bool = False

    def trigger_event(self, event: AudioEvent) -> Dict:
        """
        Aciona um evento de áudio.

        Args:
            event: Evento a ser acionado

        Returns:
            Dict com informações do áudio a ser tocado
        """
        if self.muted:
            return {"action": "none"}

        audio_config = AUDIO_LIBRARY.get(event)
        if not audio_config:
            return {"action": "none"}

        audio_type = audio_config["type"]

        # Música: fade out anterior e toca nova
        if audio_type == AudioType.MUSIC:
            return self._trigger_music(event, audio_config)

        # Ambiente: cross-fade
        elif audio_type == AudioType.AMBIENT:
            return self._trigger_ambient(event, audio_config)

        # SFX: toca diretamente
        elif audio_type == AudioType.SFX:
            return self._trigger_sfx(event, audio_config)

        return {"action": "none"}

    def _trigger_music(self, event: AudioEvent, config: Dict) -> Dict:
        """Aciona música de fundo."""
        previous = self.current_music
        self.current_music = event

        return {
            "action": "play_music",
            "file": config["file"],
            "volume": config["volume"] * self.music_volume * self.master_volume,
            "loop": config.get("loop", True),
            "fade_in": config.get("fade_in", 1000),
            "fade_out_previous": 500 if previous else 0
        }

    def _trigger_ambient(self, event: AudioEvent, config: Dict) -> Dict:
        """Aciona som ambiente."""
        previous = self.current_ambient
        self.current_ambient = event

        return {
            "action": "play_ambient",
            "file": config["file"],
            "volume": config["volume"] * self.ambient_volume * self.master_volume,
            "loop": config.get("loop", True),
            "cross_fade": 2000 if previous else 0
        }

    def _trigger_sfx(self, event: AudioEvent, config: Dict) -> Dict:
        """Aciona efeito sonoro."""
        return {
            "action": "play_sfx",
            "file": config["file"],
            "volume": config["volume"] * self.sfx_volume * self.master_volume,
            "loop": config.get("loop", False)
        }

    def stop_music(self, fade_out: int = 1000) -> Dict:
        """Para música atual."""
        self.current_music = None
        return {
            "action": "stop_music",
            "fade_out": fade_out
        }

    def stop_ambient(self, fade_out: int = 2000) -> Dict:
        """Para som ambiente."""
        self.current_ambient = None
        return {
            "action": "stop_ambient",
            "fade_out": fade_out
        }

    def set_volume(self, music: float = None, sfx: float = None, ambient: float = None, master: float = None):
        """Ajusta volumes."""
        if music is not None:
            self.music_volume = max(0.0, min(1.0, music))
        if sfx is not None:
            self.sfx_volume = max(0.0, min(1.0, sfx))
        if ambient is not None:
            self.ambient_volume = max(0.0, min(1.0, ambient))
        if master is not None:
            self.master_volume = max(0.0, min(1.0, master))

    def mute(self):
        """Muta todo áudio."""
        self.muted = True
        return {"action": "mute_all"}

    def unmute(self):
        """Desmuta áudio."""
        self.muted = False
        return {"action": "unmute_all"}

    def get_audio_for_section(self, section_content: str) -> List[Dict]:
        """
        Determina áudios ambiente baseado no conteúdo da seção.

        Args:
            section_content: Texto da seção

        Returns:
            Lista de comandos de áudio
        """
        content_lower = section_content.lower()
        audio_commands = []

        # Detectar ambiente baseado em keywords
        if any(word in content_lower for word in ["masmorra", "calabouço", "corredor escuro", "pedra", "umido"]):
            audio_commands.append(self.trigger_event(AudioEvent.AMBIENT_DUNGEON))

        elif any(word in content_lower for word in ["floresta", "árvores", "mata", "bosque", "selva"]):
            audio_commands.append(self.trigger_event(AudioEvent.AMBIENT_FOREST))

        elif any(word in content_lower for word in ["taverna", "estalagem", "bar", "bebidas"]):
            audio_commands.append(self.trigger_event(AudioEvent.AMBIENT_TAVERN))

        elif any(word in content_lower for word in ["cidade", "vila", "rua", "mercado", "praça"]):
            audio_commands.append(self.trigger_event(AudioEvent.AMBIENT_CITY))

        elif any(word in content_lower for word in ["caverna", "gruta", "mina", "túnel", "buraco"]):
            audio_commands.append(self.trigger_event(AudioEvent.AMBIENT_CAVE))

        return audio_commands


# ===== INSTÂNCIA GLOBAL =====
audio_manager = AudioManager()


# ===== HELPER FUNCTIONS =====

def trigger_audio_event(event: AudioEvent) -> Dict:
    """Wrapper para facilitar uso."""
    return audio_manager.trigger_event(event)


def get_section_audio(section_content: str) -> List[Dict]:
    """Wrapper para áudio baseado em seção."""
    return audio_manager.get_audio_for_section(section_content)
