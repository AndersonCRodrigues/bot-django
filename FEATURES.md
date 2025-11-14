# 🎮 RPG Fighting Fantasy - Features Implementadas

Documentação das funcionalidades profissionais implementadas no projeto.

---

## 📋 Índice

1. [WebSocket em Tempo Real](#websocket-em-tempo-real)
2. [Sistema de Achievements](#sistema-de-achievements)
3. [Sistema de Áudio](#sistema-de-áudio)
4. [Recuperação de Senha](#recuperação-de-senha)
5. [Agente Narrativo Híbrido](#agente-narrativo-híbrido)
6. [Como Usar](#como-usar)

---

## 1. WebSocket em Tempo Real

### 📍 Localização
`apps/game/consumers.py` | `apps/game/routing.py` | `config/asgi.py`

### ✨ Funcionalidades

- **Chat em tempo real** entre cliente e servidor
- **Streaming de narrativa** (possibilidade de narração palavra por palavra)
- **Typing indicators** (mostra quando está processando)
- **Notificações push** de eventos do jogo
- **Reconexão automática** em caso de queda

### 🔌 Como Conectar

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/game/');

ws.onopen = () => {
    console.log('Conectado!');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Recebido:', data);
};

// Enviar ação
ws.send(JSON.stringify({
    type: 'player_action',
    action: 'Eu abro a porta',
    session_id: 'SESSION_ID_AQUI'
}));
```

### 📨 Protocolo de Mensagens

**Cliente → Servidor:**
```json
{
    "type": "player_action",
    "action": "Eu abro a porta",
    "session_id": "507f1f77bcf86cd799439011"
}
```

**Servidor → Cliente:**
```json
{
    "type": "narrative",
    "content": "Você abre a porta rangente...",
    "stats": {
        "skill": 10,
        "stamina": 18,
        "luck": 9
    },
    "game_over": false
}
```

**Tipos de mensagem do servidor:**
- `connection_established` - Conexão estabelecida
- `processing` - Processando ação
- `narrative` - Resposta narrativa
- `error` - Erro
- `achievement` - Achievement desbloqueado
- `game_over` - Fim de jogo
- `notification` - Notificação geral
- `typing` - Indicator de digitação

---

## 2. Sistema de Achievements

### 📍 Localização
`apps/game/achievements.py`

### 🏆 Categorias

1. **Combate** ⚔️
   - Primeiro Sangue
   - Guerreiro
   - Invicto

2. **Exploração** 🗺️
   - Explorador
   - Completista
   - Corredor Veloz

3. **Sobrevivência** 🍀
   - Sobrevivente Sortudo

4. **Coleção** 🎒
   - Acumulador
   - Rico

5. **História** 📖
   - Primeira Aventura
   - Veterano (hidden)

6. **Especial** ✨
   - Homem de Ferro (hidden)
   - Speedrunner (hidden)
   - Perfeccionista (hidden)

### 💻 Como Usar

```python
from apps.game.achievements import check_achievements, get_user_achievements

# Verificar achievements desbloqueados
newly_unlocked = check_achievements(
    user_id=user.id,
    session=game_session,
    character=character
)

for achievement in newly_unlocked:
    print(f"🏆 {achievement.name} - {achievement.description}")
    # Enviar notificação via WebSocket
    channel_layer.group_send(
        f"game_group_{user.id}",
        {
            "type": "achievement_unlocked",
            "achievement": achievement.to_dict()
        }
    )

# Obter todos achievements do usuário
achievements = get_user_achievements(user_id=user.id)
# Retorna lista com {"id": ..., "name": ..., "unlocked": True/False}

# Estatísticas
stats = get_achievement_stats(user_id=user.id)
# {"total": 13, "unlocked": 5, "points": 150, "completion_rate": 38.5}
```

---

## 3. Sistema de Áudio

### 📍 Localização
`apps/game/audio_manager.py`

### 🎵 Tipos de Áudio

1. **Música** 🎼 - Temas de fundo
2. **SFX** 🔊 - Efeitos sonoros
3. **Ambiente** 🌲 - Sons ambientes contínuos
4. **Voz** 🎙️ - Narração (futuro)

### 🎯 Eventos Suportados

**Combate:**
- `COMBAT_START` - Inicia tema de combate
- `COMBAT_HIT` - Som de acerto
- `COMBAT_MISS` - Som de erro
- `COMBAT_VICTORY` - Som de vitória
- `COMBAT_DEFEAT` - Música de derrota

**Itens:**
- `ITEM_PICKUP` - Pegar item
- `ITEM_USE` - Usar item
- `ITEM_DROP` - Soltar item

**Interação:**
- `DOOR_OPEN` - Abrir porta
- `DOOR_LOCKED` - Porta trancada

**Testes:**
- `TEST_SUCCESS` - Teste bem-sucedido
- `TEST_FAILURE` - Teste falhou

**Ambiente:**
- `AMBIENT_DUNGEON` - Masmorra
- `AMBIENT_FOREST` - Floresta
- `AMBIENT_TAVERN` - Taverna
- `AMBIENT_CITY` - Cidade
- `AMBIENT_CAVE` - Caverna

### 💻 Como Usar

```python
from apps.game.audio_manager import trigger_audio_event, AudioEvent

# Acionar evento
audio_command = trigger_audio_event(AudioEvent.COMBAT_START)
# Retorna: {
#     "action": "play_music",
#     "file": "audio/music/combat_theme.mp3",
#     "volume": 0.7,
#     "loop": True,
#     "fade_in": 500
# }

# Enviar comando para cliente via WebSocket
await self.send(text_data=json.dumps({
    "type": "audio",
    "command": audio_command
}))

# Áudio baseado em seção
from apps.game.audio_manager import get_section_audio

audio_commands = get_section_audio("Você entra numa masmorra escura...")
# Retorna lista de comandos de áudio ambiente
```

### 🎛️ Controles

```python
from apps.game.audio_manager import audio_manager

# Ajustar volumes
audio_manager.set_volume(music=0.7, sfx=0.8, ambient=0.3, master=1.0)

# Mute/Unmute
audio_manager.mute()
audio_manager.unmute()

# Parar música/ambiente
audio_manager.stop_music(fade_out=1000)
audio_manager.stop_ambient(fade_out=2000)
```

---

## 4. Recuperação de Senha

### 📍 Localização
`apps/accounts/views.py` | `apps/accounts/urls.py` | `templates/accounts/password_reset*.html`

### 🔐 Fluxo Completo

1. **Solicitar Reset** → `/accounts/password-reset/`
2. **Email Enviado** → Confirmação
3. **Link no Email** → Token único de 24h
4. **Definir Nova Senha** → `/accounts/password-reset-confirm/<token>/`
5. **Confirmação** → Senha redefinida

### 🎨 UI Mobile-First

- Gradientes modernos
- Responsivo (mobile/desktop)
- Feedback visual claro
- Validação em tempo real

### ⚙️ Configuração

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu@email.com'
EMAIL_HOST_PASSWORD = 'sua_senha_app'
DEFAULT_FROM_EMAIL = 'RPG Adventure <noreply@rpg.com>'
```

### 📧 Templates de Email

- `password_reset_subject.txt` - Assunto
- `password_reset_email.html` - Corpo do email

---

## 5. Agente Narrativo Híbrido

### 📍 Localização
`apps/game/workflows/narrative_agent.py`

### 🎭 Filosofia: Liberdade + Estrutura

**✅ LIBERDADE CRIATIVA:**

1. **Diálogos Ricos**
   - NPCs com personalidade
   - Conversas naturais (não menu de opções)
   - Revelam dicas sutis

2. **Descrições Sensoriais**
   - Cheiros, sons, texturas
   - Atmosfera e tensão
   - Detalhes visuais

3. **Combate Tático**
   - Aceita táticas criativas
   - Narrativa cinematográfica
   - Mecânica de dados permanece igual

4. **Exploração Livre**
   - Examinar qualquer coisa
   - Flavor text rico
   - Resposta interessante mesmo para itens inexistentes

**❌ RESTRIÇÕES RÍGIDAS:**

1. **Itens**
   - Apenas da whitelist do livro
   - Só encontra se estiver na seção
   - Não inventa itens

2. **Navegação**
   - Apenas seções conectadas
   - Validação de caminhos
   - Progressão linear

3. **Mecânica**
   - Dados são lei absoluta
   - Stats não mudam arbitrariamente
   - Regras Fighting Fantasy

4. **NPCs**
   - Personalidade do livro
   - Motivações originais
   - Informações limitadas

### 💻 Como Usar

```python
from apps.game.workflows.narrative_agent import generate_hybrid_narrative

narrative = generate_hybrid_narrative(
    player_action="Eu falo com o barman sobre o vampiro",
    character_name="Aragorn",
    skill=10,
    stamina=18,
    initial_stamina=20,
    luck=9,
    gold=5,
    inventory=["espada", "poção"],
    current_section=23,
    section_content="Você está na taverna...",
    recent_history="Turno 1: entrou na taverna\nTurno 2: sentou no balcão",
    flags={"tavern_visited": True},
    book_class_name="Warlock_of_Firetop_Mountain",
    in_combat=False
)

print(narrative)
# "O barman, um homem corpulento com uma cicatriz no rosto,
# olha para você desconfiado. 'Vampiro?' ele murmura baixo,
# 'Cuidado ao mencionar essa criatura aqui. Dizem que ele
# vive no cemitério ao norte...' Ele desliza uma moeda de
# ouro pela mesa. 'Tome, você vai precisar.'"
```

### 🛡️ Validadores

```python
from apps.game.workflows.narrative_agent import RigidStructureValidator

validator = RigidStructureValidator("Warlock_of_Firetop_Mountain")

# Validar navegação
result = validator.validate_navigation(
    current_section=23,
    target_section=45,
    visited_sections=[1, 23],
    flags={}
)
# {"valid": True, "error_message": None, "reason": "ok"}

# Validar item
result = validator.validate_item_pickup(
    item_name="espada_magica",
    current_section=23,
    inventory=["escudo"]
)

# Validar ação geral
result = validator.validate_action(
    player_action="Eu abro a porta",
    current_section=23,
    flags={"has_key": False, "door_locked": True},
    in_combat=False
)
# {"valid": False, "error_message": "A porta está trancada. Você precisa encontrar a chave.", "reason": "missing_key"}
```

---

## 6. Como Usar

### 🚀 Início Rápido

1. **Instalar Dependências**
```bash
pip install channels channels-redis django-redis
```

2. **Iniciar Redis**
```bash
docker run -p 6379:6379 redis:alpine
```

3. **Rodar Servidor**
```bash
python manage.py runserver
```

4. **Testar WebSocket**
- Abrir console do navegador
- Conectar ao `ws://localhost:8000/ws/game/`

### 🎮 Integração no Jogo

```python
# views.py
from apps.game.achievements import check_achievements
from apps.game.audio_manager import trigger_audio_event, AudioEvent
from apps.game.workflows.narrative_agent import generate_hybrid_narrative

def process_turn(request, session_id):
    # 1. Processar ação
    result = process_game_action(session_id, request.user.id, player_action)

    # 2. Verificar achievements
    achievements = check_achievements(request.user.id, session, character)
    for ach in achievements:
        # Notificar via WebSocket
        notify_achievement(request.user.id, ach)

    # 3. Determinar áudio
    audio_commands = []
    if result["in_combat"]:
        audio_commands.append(trigger_audio_event(AudioEvent.COMBAT_START))

    # 4. Retornar resposta
    return JsonResponse({
        "narrative": result["narrative"],
        "stats": result["stats"],
        "achievements": [a.to_dict() for a in achievements],
        "audio": audio_commands
    })
```

### 📱 Cliente (JavaScript)

```javascript
// Conectar
const ws = new WebSocket('ws://localhost:8000/ws/game/');

// Enviar ação
function sendAction(action) {
    ws.send(JSON.stringify({
        type: 'player_action',
        action: action,
        session_id: SESSION_ID
    }));
}

// Receber resposta
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'narrative':
            displayNarrative(data.content);
            updateStats(data.stats);
            playAudio(data.audio);
            break;

        case 'achievement':
            showAchievementPopup(data.achievement);
            break;

        case 'game_over':
            handleGameOver(data);
            break;
    }
};
```

---

## 🎯 Roadmap

### ✅ Concluído
- WebSocket em tempo real
- Sistema de achievements
- Sistema de áudio
- Recuperação de senha
- Agente narrativo híbrido

### 🚧 Em Progresso
- Interface de jogo com WebSocket
- Integração completa de achievements no workflow
- Sistema de save/load múltiplo

### 📝 Próximos Passos
- Testes unitários
- Documentação de API
- PWA (Progressive Web App)
- Notificações push nativas
- Sistema de ranking
- Multiplayer (espectadores)

---

## 📞 Suporte

- **Bugs**: Abrir issue no GitHub
- **Features**: Pull request
- **Dúvidas**: Documentação do código

---

**Desenvolvido com ❤️ para criar a melhor experiência de RPG Fighting Fantasy digital**
