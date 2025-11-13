# ============================================
# CONFIGURAÇÕES
# ============================================
PYTHON=python3.11
VENV=.venv
PORT ?= 8000
DJANGO_SETTINGS=config.settings.development

# Cores para output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

# ============================================
# SETUP INICIAL
# ============================================
.PHONY: help
help:
	@echo "$(GREEN)Comandos disponíveis:$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make setup          - Setup completo do projeto"
	@echo "  make venv           - Criar ambiente virtual"
	@echo "  make install        - Instalar dependências"
	@echo "  make requirements   - Gerar requirements.txt"
	@echo ""
	@echo "$(YELLOW)Desenvolvimento:$(NC)"
	@echo "  make run            - Rodar servidor Django"
	@echo "  make runserver      - Alias para run"
	@echo "  make shell          - Django shell"
	@echo "  make migrate        - Aplicar migrations"
	@echo "  make makemigrations - Criar migrations"
	@echo "  make createsuperuser - Criar superusuário"
	@echo ""
	@echo "$(YELLOW)Databases:$(NC)"
	@echo "  make mongodb        - Iniciar MongoDB (Docker)"
	@echo "  make redis          - Iniciar Redis (Docker)"
	@echo "  make weaviate       - Iniciar Weaviate (Docker)"
	@echo "  make dbs            - Iniciar todos os databases"
	@echo "  make dbs-stop       - Parar todos os databases"
	@echo ""
	@echo "$(YELLOW)Celery:$(NC)"
	@echo "  make celery         - Iniciar Celery worker"
	@echo "  make celery-beat    - Iniciar Celery beat"
	@echo "  make flower         - Iniciar Flower (monitor Celery)"
	@echo ""
	@echo "$(YELLOW)Frontend (Tailwind):$(NC)"
	@echo "  make tailwind-install - Instalar Tailwind"
	@echo "  make tailwind-watch   - Compilar Tailwind (watch mode)"
	@echo "  make tailwind-build   - Build Tailwind para produção"
	@echo ""
	@echo "$(YELLOW)Testes e Qualidade:$(NC)"
	@echo "  make test           - Rodar testes"
	@echo "  make coverage       - Rodar testes com coverage"
	@echo "  make lint           - Rodar linter"
	@echo "  make format         - Formatar código"
	@echo ""
	@echo "$(YELLOW)Limpeza:$(NC)"
	@echo "  make clean          - Limpar arquivos temporários"
	@echo "  make clean-all      - Limpar tudo (incluindo venv)"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  make docker-build   - Build imagem Docker"
	@echo "  make docker-run     - Rodar container"
	@echo ""
	@echo "$(YELLOW)Deploy:$(NC)"
	@echo "  make collectstatic  - Coletar arquivos estáticos"
	@echo "  make check          - Verificar deploy"

# ============================================
# SETUP INICIAL
# ============================================
.PHONY: setup
setup: venv install migrate
	@echo "$(GREEN)✓ Setup completo!$(NC)"
	@echo "$(YELLOW)Próximos passos:$(NC)"
	@echo "  1. Configure seu .env com as chaves necessárias"
	@echo "  2. make dbs (iniciar databases)"
	@echo "  3. make createsuperuser (criar admin)"
	@echo "  4. make run (iniciar servidor)"

.PHONY: venv
venv:
	@echo "$(YELLOW)Criando ambiente virtual...$(NC)"
	@$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✓ Ambiente virtual criado em .venv/$(NC)"
	@echo "$(YELLOW)Ative com: source $(VENV)/bin/activate$(NC)"

.PHONY: install
install:
	@echo "$(YELLOW)Instalando dependências...$(NC)"
	@$(VENV)/bin/pip install --upgrade pip
	@$(VENV)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependências instaladas!$(NC)"

.PHONY: requirements
requirements:
	@echo "$(YELLOW)Gerando requirements.txt...$(NC)"
	@$(VENV)/bin/pip freeze > requirements.txt
	@echo "$(GREEN)✓ requirements.txt atualizado!$(NC)"

# ============================================
# DESENVOLVIMENTO
# ============================================
.PHONY: run runserver
run: runserver
runserver:
	@echo "$(GREEN)Iniciando servidor Django...$(NC)"
	@$(VENV)/bin/python manage.py runserver 0.0.0.0:$(PORT) --settings=$(DJANGO_SETTINGS)

.PHONY: shell
shell:
	@$(VENV)/bin/python manage.py shell_plus --settings=$(DJANGO_SETTINGS)

.PHONY: migrate
migrate:
	@echo "$(YELLOW)Aplicando migrations...$(NC)"
	@$(VENV)/bin/python manage.py migrate --settings=$(DJANGO_SETTINGS)
	@echo "$(GREEN)✓ Migrations aplicadas!$(NC)"

.PHONY: makemigrations
makemigrations:
	@echo "$(YELLOW)Criando migrations...$(NC)"
	@$(VENV)/bin/python manage.py makemigrations --settings=$(DJANGO_SETTINGS)
	@echo "$(GREEN)✓ Migrations criadas!$(NC)"

.PHONY: createsuperuser
createsuperuser:
	@echo "$(YELLOW)Criando superusuário...$(NC)"
	@$(VENV)/bin/python manage.py createsuperuser --settings=$(DJANGO_SETTINGS)

.PHONY: showmigrations
showmigrations:
	@$(VENV)/bin/python manage.py showmigrations --settings=$(DJANGO_SETTINGS)

# ============================================
# DATABASES (Docker)
# ============================================
.PHONY: mongodb
mongodb:
	@echo "$(YELLOW)Iniciando MongoDB...$(NC)"
	@docker run -d \
		--name rpg-mongodb \
		-p 27017:27017 \
		-e MONGO_INITDB_ROOT_USERNAME=admin \
		-e MONGO_INITDB_ROOT_PASSWORD=admin123 \
		-v mongodb_data:/data/db \
		mongo:latest
	@echo "$(GREEN)✓ MongoDB rodando em localhost:27017$(NC)"

.PHONY: redis
redis:
	@echo "$(YELLOW)Verificando porta 6379...$(NC)"
	@if lsof -i :6379 > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Redis já está rodando em localhost:6379$(NC)"; \
	else \
		echo "$(YELLOW)Iniciando Redis via Docker...$(NC)"; \
		docker run -d \
			--name rpg-redis \
			-p 6379:6379 \
			redis:alpine; \
		echo "$(GREEN)✓ Redis Docker rodando em localhost:6379$(NC)"; \
	fi

.PHONY: weaviate
weaviate:
	@echo "$(YELLOW)Iniciando Weaviate...$(NC)"
	@docker run -d \
		--name rpg-weaviate \
		-p 8080:8080 \
		-p 50051:50051 \
		-e QUERY_DEFAULTS_LIMIT=20 \
		-e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
		-e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
		-e DEFAULT_VECTORIZER_MODULE=text2vec-transformers \
		-e ENABLE_MODULES=text2vec-transformers \
		-v weaviate_data:/var/lib/weaviate \
		semitechnologies/weaviate:latest
	@echo "$(GREEN)✓ Weaviate rodando em localhost:8080$(NC)"

.PHONY: dbs
dbs: mongodb redis weaviate
	@echo "$(GREEN)✓ Todos os databases iniciados!$(NC)"

.PHONY: dbs-stop
dbs-stop:
	@echo "$(YELLOW)Parando databases...$(NC)"
	@docker stop rpg-mongodb rpg-redis rpg-weaviate || true
	@echo "$(GREEN)✓ Databases parados!$(NC)"

.PHONY: dbs-remove
dbs-remove: dbs-stop
	@echo "$(YELLOW)Removendo containers...$(NC)"
	@docker rm rpg-mongodb rpg-redis rpg-weaviate || true
	@echo "$(GREEN)✓ Containers removidos!$(NC)"

.PHONY: dbs-logs
dbs-logs:
	@echo "$(YELLOW)Logs dos databases:$(NC)"
	@docker logs rpg-mongodb --tail 50 -f

# ============================================
# CELERY
# ============================================
.PHONY: celery
celery:
	@echo "$(GREEN)Iniciando Celery worker...$(NC)"
	@$(VENV)/bin/celery -A config worker --loglevel=info

.PHONY: celery-beat
celery-beat:
	@echo "$(GREEN)Iniciando Celery beat...$(NC)"
	@$(VENV)/bin/celery -A config beat --loglevel=info

.PHONY: flower
flower:
	@echo "$(GREEN)Iniciando Flower...$(NC)"
	@$(VENV)/bin/celery -A config flower --port=5555

.PHONY: celery-all
celery-all:
	@echo "$(GREEN)Iniciando Celery worker + beat...$(NC)"
	@$(VENV)/bin/celery -A config worker --beat --loglevel=info

# ============================================
# FRONTEND - TAILWIND
# ============================================
.PHONY: tailwind-install
tailwind-install:
	@echo "$(YELLOW)Instalando Tailwind CSS...$(NC)"
	@npm install -D tailwindcss@latest postcss@latest autoprefixer@latest
	@npm install -D @tailwindcss/forms @tailwindcss/typography
	@npm install -D daisyui@latest
	@npm install htmx.org alpinejs
	@npx tailwindcss init -p
	@echo "$(GREEN)✓ Tailwind instalado!$(NC)"

.PHONY: tailwind-watch
tailwind-watch:
	@echo "$(GREEN)Compilando Tailwind (watch mode)...$(NC)"
	@npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch

.PHONY: tailwind-build
tailwind-build:
	@echo "$(YELLOW)Build Tailwind para produção...$(NC)"
	@npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --minify
	@echo "$(GREEN)✓ Tailwind compilado!$(NC)"

# ============================================
# TESTES E QUALIDADE
# ============================================
.PHONY: test
test:
	@echo "$(YELLOW)Rodando testes...$(NC)"
	@$(VENV)/bin/python manage.py test --settings=$(DJANGO_SETTINGS)

.PHONY: coverage
coverage:
	@echo "$(YELLOW)Rodando testes com coverage...$(NC)"
	@$(VENV)/bin/coverage run --source='.' manage.py test --settings=$(DJANGO_SETTINGS)
	@$(VENV)/bin/coverage report
	@$(VENV)/bin/coverage html
	@echo "$(GREEN)✓ Relatório em htmlcov/index.html$(NC)"

.PHONY: lint
lint:
	@echo "$(YELLOW)Rodando linter...$(NC)"
	@$(VENV)/bin/flake8 apps/ config/
	@$(VENV)/bin/pylint apps/ config/

.PHONY: format
format:
	@echo "$(YELLOW)Formatando código...$(NC)"
	@$(VENV)/bin/black apps/ config/
	@$(VENV)/bin/isort apps/ config/
	@echo "$(GREEN)✓ Código formatado!$(NC)"

# ============================================
# LIMPEZA
# ============================================
.PHONY: clean
clean:
	@echo "$(YELLOW)Limpando arquivos temporários...$(NC)"
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@find . -type d -name '*.egg-info' -exec rm -rf {} +
	@rm -rf .pytest_cache
	@rm -rf .coverage
	@rm -rf htmlcov
	@rm -rf dist
	@rm -rf build
	@echo "$(GREEN)✓ Arquivos temporários removidos!$(NC)"

.PHONY: clean-all
clean-all: clean
	@echo "$(RED)Removendo ambiente virtual...$(NC)"
	@rm -rf $(VENV)
	@rm -rf node_modules
	@rm -rf staticfiles
	@echo "$(GREEN)✓ Limpeza completa!$(NC)"

# ============================================
# DOCKER
# ============================================
.PHONY: docker-build
docker-build:
	@echo "$(YELLOW)Building Docker image...$(NC)"
	@docker build -t rpg-django-app .
	@echo "$(GREEN)✓ Imagem criada!$(NC)"

.PHONY: docker-run
docker-run:
	@echo "$(GREEN)Rodando container...$(NC)"
	@docker run -d -p $(PORT):8000 --env-file .env rpg-django-app

# ============================================
# DEPLOY
# ============================================
.PHONY: collectstatic
collectstatic:
	@echo "$(YELLOW)Coletando arquivos estáticos...$(NC)"
	@$(VENV)/bin/python manage.py collectstatic --noinput --settings=config.settings.production
	@echo "$(GREEN)✓ Arquivos estáticos coletados!$(NC)"

.PHONY: check
check:
	@echo "$(YELLOW)Verificando configuração para deploy...$(NC)"
	@$(VENV)/bin/python manage.py check --deploy --settings=config.settings.production

.PHONY: deploy
deploy: clean tailwind-build collectstatic
	@echo "$(GREEN)✓ Pronto para deploy!$(NC)"

# ============================================
# DEV COMPLETO
# ============================================
.PHONY: dev
dev:
	@echo "$(GREEN)Iniciando ambiente de desenvolvimento completo...$(NC)"
	@make -j 3 runserver celery tailwind-watch