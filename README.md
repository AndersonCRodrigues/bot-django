# 🎮 RPG Fighting Fantasy - Edição Digital Profissional

Sistema completo de RPG baseado nos livros-jogos Fighting Fantasy de Steve Jackson, com inteligência artificial, narrativa dinâmica e recursos profissionais.

---

## 🌟 Destaques

- 🤖 **IA Narrativa Híbrida** - Liberdade criativa dentro de estrutura rígida do livro
- ⚡ **WebSocket em Tempo Real** - Chat instantâneo e notificações
- 🏆 **Sistema de Achievements** - 13+ conquistas para desbloquear
- 🎵 **Áudio Dinâmico** - Música e efeitos contextuais
- 📱 **Mobile-First** - Design responsivo profissional
- 🎲 **Mecânica Fiel** - Regras originais de Fighting Fantasy
- 🔐 **Sistema Completo** - Auth, recuperação de senha, perfis

---

## 🏗️ Arquitetura

```
Django 4.x + Channels (WebSocket)
├── MongoDB (sessões/personagens)
├── Weaviate (RAG para livros)
├── Redis (cache/channels)
├── Gemini 1.5 Flash (narrativa IA)
└── LangGraph (workflow)
```

### Stack Completo

**Backend:**
- Django 4.x
- Django Channels (WebSocket ASGI)
- LangGraph (workflow AI)
- MongoDB (Motor async)
- Weaviate (vector DB)
- Redis (cache + channels)
- Celery (tasks assíncronas)

**Frontend:**
- TailwindCSS
- Vanilla JavaScript (WebSocket nativo)
- Design Mobile-First

**IA:**
- Google Gemini 1.5 Flash
- LangChain
- RAG (Retrieval-Augmented Generation)

---

## 🚀 Setup Rápido

### 1. Pré-requisitos

```bash
# Python 3.11+
python --version

# Docker (para serviços)
docker --version

# Git
git --version
```

### 2. Clonar e Instalar

```bash
# Clone
git clone https://github.com/AndersonCRodrigues/bot-django.git
cd bot-django

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Dependências
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente

Crie `.env` na raiz:

```env
# Django
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=rpg_database

# Redis
REDIS_URL=redis://localhost:6379/0
CHANNELS_REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051
WEAVIATE_SECURE=False

# Google Gemini
GOOGLE_API_KEY=sua_api_key_gemini

# Email (opcional - para password reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu@email.com
EMAIL_HOST_PASSWORD=sua_senha_app
```

### 4. Iniciar Serviços

```bash
# Docker Compose (MongoDB + Redis + Weaviate)
docker-compose up -d

# Ou manualmente:
docker run -d -p 27017:27017 --name mongo mongo:latest
docker run -d -p 6379:6379 --name redis redis:alpine
docker run -d -p 8080:8080 -p 50051:50051 --name weaviate semitechnologies/weaviate:latest
```

### 5. Migrations e Dados

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Collect static
python manage.py collectstatic --noinput
```

### 6. Rodar Servidor

```bash
# Servidor Django (ASGI com Daphne)
python manage.py runserver

# Em outro terminal: Celery (opcional)
celery -A config worker -l info

# Acesse: http://localhost:8000
```

---

## 📚 Como Jogar

### 1. Criar Conta
- Acesse `/accounts/register/`
- Cadastre-se (username, email, senha)

### 2. Criar Personagem
- Vá para "Personagens" → "Criar Novo"
- Role os dados: HABILIDADE, ENERGIA, SORTE
- Dê um nome ao personagem

### 3. Escolher Aventura
- Vá para "Aventuras"
- Escolha um livro (ex: Warlock of Firetop Mountain)
- Clique em "Jogar"

### 4. Jogar!
- Digite ações em linguagem natural
- Exemplos:
  - "Eu abro a porta e entro"
  - "Atacar o goblin"
  - "Examinar a sala cuidadosamente"
  - "Conversar com o barman sobre o vampiro"
  - "Testar sorte"

---

## 🎮 Features Principais

### 1. WebSocket em Tempo Real

```javascript
// Cliente JavaScript
const ws = new WebSocket('ws://localhost:8000/ws/game/');

ws.send(JSON.stringify({
    type: 'player_action',
    action: 'Eu abro a porta',
    session_id: 'SESSION_ID'
}));

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.content); // Narrativa
};
```

### 2. Sistema de Achievements

- 🗡️ **Combate**: Primeiro Sangue, Guerreiro, Invicto
- 🗺️ **Exploração**: Explorador, Completista, Corredor Veloz
- 🍀 **Sobrevivência**: Sobrevivente Sortudo
- 🎒 **Coleção**: Acumulador, Rico
- 📖 **História**: Primeira Aventura, Veterano
- ✨ **Especial**: Homem de Ferro, Speedrunner, Perfeccionista

### 3. Áudio Dinâmico

- Música de fundo automática
- Efeitos sonoros (combate, itens, portas)
- Ambiente baseado em localização
- Controles de volume independentes

### 4. Agente Narrativo Híbrido

**Liberdade Criativa:**
- Diálogos ricos com NPCs
- Descrições sensoriais (cheiros, sons, texturas)
- Combate tático e descritivo
- Exploração livre

**Estrutura Rígida:**
- Navegação apenas em seções conectadas
- Itens somente da whitelist do livro
- Progressão linear
- Mecânica de dados imutável
- NPCs fiéis ao livro

---

## 📖 Documentação

- **[FEATURES.md](./FEATURES.md)** - Documentação completa de features
- **[API.md](./docs/API.md)** - Documentação da API (em breve)
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - Arquitetura do sistema (em breve)

---

## 🛠️ Desenvolvimento

### Estrutura de Diretórios

```
bot-django/
├── apps/
│   ├── accounts/          # Autenticação e usuários
│   ├── characters/        # Personagens (MongoDB)
│   ├── adventures/        # Aventuras/Livros
│   └── game/
│       ├── consumers.py   # WebSocket consumer
│       ├── achievements.py
│       ├── audio_manager.py
│       ├── workflows/     # LangGraph workflows
│       ├── tools/         # Ferramentas (dados, combate)
│       └── prompts/       # Prompts do Gemini
├── config/
│   ├── settings/
│   ├── urls.py
│   └── asgi.py           # ASGI config (WebSocket)
├── templates/            # Templates Django
├── static/              # CSS, JS, assets
├── media/               # Uploads
└── requirements.txt
```

### Rodar Testes

```bash
# Todos os testes
python manage.py test

# App específico
python manage.py test apps.game

# Com cobertura
coverage run --source='.' manage.py test
coverage report
```

### Linting

```bash
# Black (formatter)
black .

# Flake8 (linter)
flake8 .

# isort (imports)
isort .
```

---

## 🌐 Deploy

### Heroku

```bash
# Login
heroku login

# Criar app
heroku create seu-app-rpg

# Addons
heroku addons:create heroku-redis:mini
heroku addons:create mongolab:sandbox

# Config vars
heroku config:set SECRET_KEY=...
heroku config:set GOOGLE_API_KEY=...

# Deploy
git push heroku main

# Migrate
heroku run python manage.py migrate
```

### Docker

```bash
# Build
docker build -t rpg-fighting-fantasy .

# Run
docker run -p 8000:8000 rpg-fighting-fantasy
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Guidelines

- Seguir PEP 8
- Adicionar testes
- Documentar código
- Atualizar FEATURES.md se adicionar feature

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja [LICENSE](./LICENSE) para mais detalhes.

---

## 🙏 Créditos

- **Steve Jackson** - Criador de Fighting Fantasy
- **Fighting Fantasy Gamebooks** - Inspiração original
- **Google Gemini** - IA narrativa
- **Weaviate** - Vector database
- **LangChain** - Framework de IA

---

## 📞 Contato

- **GitHub**: [@AndersonCRodrigues](https://github.com/AndersonCRodrigues)
- **Email**: anderson@example.com
- **Issues**: [GitHub Issues](https://github.com/AndersonCRodrigues/bot-django/issues)

---

## 🎯 Roadmap

### ✅ Versão 1.0 (Atual)
- [x] WebSocket em tempo real
- [x] Sistema de achievements
- [x] Sistema de áudio
- [x] Recuperação de senha
- [x] Agente narrativo híbrido
- [x] Design mobile-first

### 🚧 Versão 1.1 (Em Breve)
- [ ] Interface de jogo completa com WebSocket
- [ ] Integração de achievements no gameplay
- [ ] Sistema de save/load múltiplo
- [ ] Testes unitários completos

### 📝 Versão 2.0 (Futuro)
- [ ] PWA (Progressive Web App)
- [ ] Notificações push nativas
- [ ] Sistema de ranking
- [ ] Multiplayer (modo espectador)
- [ ] Narração por voz (TTS)
- [ ] Suporte a mais livros Fighting Fantasy
- [ ] Editor de aventuras customizadas

---

**Desenvolvido com ❤️ para reviver a magia dos Fighting Fantasy**

🎲 Boa sorte, aventureiro!
