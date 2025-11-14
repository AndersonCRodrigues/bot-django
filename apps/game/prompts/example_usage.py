"""
Exemplo de uso do prompt Game Master com LangChain.

Este arquivo demonstra como integrar o prompt do GM com o agente LangChain
em uma aplicação Django.
"""

from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from apps.game.tools import (
    get_character_state,
    update_character_stats,
    add_item,
    remove_item,
    check_item,
    use_item,
    roll_dice,
    # check_luck,      # Opcional: comentado se preferir modo manual
    # check_skill,     # Opcional: comentado se preferir modo manual
    # combat_round,    # Opcional: comentado se preferir combate manual
    start_combat,
    get_current_section,
    try_move_to,
)
from apps.game.prompts import get_game_master_prompt


class GameMasterAgent:
    """
    Agente Game Master que conduz a aventura usando LangChain.
    """

    def __init__(self, character_id: str, adventure_name: str):
        """
        Inicializa o agente GM.

        Args:
            character_id: ID do personagem no MongoDB
            adventure_name: Nome da aventura (classe Weaviate)
        """
        self.character_id = character_id
        self.adventure_name = adventure_name
        self.chat_history = []

        # Configurar LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.7,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        # Configurar ferramentas
        self.tools = [
            get_character_state,
            update_character_stats,
            add_item,
            remove_item,
            check_item,
            use_item,
            roll_dice,
            start_combat,
            get_current_section,
            try_move_to,
            # Opcional: adicione check_luck, check_skill, combat_round
            # se quiser permitir modo automático
        ]

        # Gerar prompt do GM
        system_prompt = get_game_master_prompt(
            character_id=character_id, adventure_name=adventure_name
        )

        # Criar prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        # Criar agente
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt_template)

        # Criar executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # Útil para debug
            handle_parsing_errors=True,
            max_iterations=15,  # Permitir múltiplas chamadas de ferramentas
            return_intermediate_steps=True,  # Retornar detalhes das chamadas
        )

    def send_message(self, user_input: str) -> dict:
        """
        Envia uma mensagem ao GM e recebe a resposta.

        Args:
            user_input: Input do jogador

        Returns:
            dict: {
                'output': str (resposta do GM),
                'intermediate_steps': list (passos intermediários),
                'chat_history': list (histórico completo)
            }
        """
        # Executar agente
        response = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": self.chat_history,
        })

        # Atualizar histórico
        self.chat_history.append(HumanMessage(content=user_input))
        self.chat_history.append(AIMessage(content=response["output"]))

        return {
            "output": response["output"],
            "intermediate_steps": response.get("intermediate_steps", []),
            "chat_history": self.chat_history,
        }

    def start_adventure(self, starting_section: int = 1) -> dict:
        """
        Inicia a aventura a partir de uma seção.

        Args:
            starting_section: Número da seção inicial (padrão: 1)

        Returns:
            dict com a resposta inicial do GM
        """
        initial_prompt = f"Iniciar aventura na seção {starting_section}"
        return self.send_message(initial_prompt)

    def reset_history(self):
        """Limpa o histórico de conversação."""
        self.chat_history = []


# ========== Exemplo de Uso em uma View Django ==========

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


# Cache de agentes por sessão (em produção, use Redis ou similar)
_agent_cache = {}


@csrf_exempt
@require_http_methods(["POST"])
def game_message_view(request):
    """
    Endpoint para enviar mensagens ao GM.

    POST /api/game/message/
    Body: {
        "character_id": "507f1f77bcf86cd799439011",
        "adventure_name": "FeiticeiroDaMontanhaFogo",
        "message": "Vou seguir o corredor à esquerda",
        "session_id": "abc123"  # Opcional: para manter histórico
    }

    Response: {
        "output": "Você segue pelo corredor...",
        "intermediate_steps": [...],
        "success": true
    }
    """
    try:
        data = json.loads(request.body)
        character_id = data.get("character_id")
        adventure_name = data.get("adventure_name")
        message = data.get("message")
        session_id = data.get("session_id")

        if not all([character_id, adventure_name, message]):
            return JsonResponse(
                {"error": "character_id, adventure_name e message são obrigatórios"},
                status=400,
            )

        # Obter ou criar agente
        cache_key = f"{session_id or character_id}_{adventure_name}"

        if cache_key not in _agent_cache:
            _agent_cache[cache_key] = GameMasterAgent(
                character_id=character_id, adventure_name=adventure_name
            )

        agent = _agent_cache[cache_key]

        # Enviar mensagem
        response = agent.send_message(message)

        return JsonResponse(
            {
                "output": response["output"],
                "intermediate_steps": [
                    {"tool": step[0].tool, "input": step[0].tool_input}
                    for step in response["intermediate_steps"]
                ],
                "success": True,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e), "success": False}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_adventure_view(request):
    """
    Endpoint para iniciar uma nova aventura.

    POST /api/game/start/
    Body: {
        "character_id": "507f1f77bcf86cd799439011",
        "adventure_name": "FeiticeiroDaMontanhaFogo",
        "session_id": "abc123"
    }

    Response: {
        "output": "Bem-vindo à aventura...",
        "success": true
    }
    """
    try:
        data = json.loads(request.body)
        character_id = data.get("character_id")
        adventure_name = data.get("adventure_name")
        session_id = data.get("session_id")

        if not all([character_id, adventure_name]):
            return JsonResponse(
                {"error": "character_id e adventure_name são obrigatórios"}, status=400
            )

        # Criar novo agente
        cache_key = f"{session_id or character_id}_{adventure_name}"
        agent = GameMasterAgent(character_id=character_id, adventure_name=adventure_name)
        _agent_cache[cache_key] = agent

        # Iniciar aventura
        response = agent.start_adventure()

        return JsonResponse({"output": response["output"], "success": True})

    except Exception as e:
        return JsonResponse({"error": str(e), "success": False}, status=500)


# ========== Exemplo de Uso em Shell/Script ==========

if __name__ == "__main__":
    """
    Exemplo de uso direto para testes.

    Execute:
        python -m apps.game.prompts.example_usage
    """
    import django
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()

    # Criar agente
    agent = GameMasterAgent(
        character_id="507f1f77bcf86cd799439011",
        adventure_name="FeiticeiroDaMontanhaFogo",
    )

    # Iniciar aventura
    print("=== INICIANDO AVENTURA ===\n")
    response = agent.start_adventure()
    print(response["output"])
    print("\n" + "=" * 50 + "\n")

    # Simular algumas interações
    interactions = [
        "Examinar a sala",
        "Seguir o corredor à esquerda",
        "Abrir a porta",
        "7",  # Resposta a uma rolagem [ROLE 2d6]
    ]

    for user_input in interactions:
        print(f"JOGADOR: {user_input}\n")
        response = agent.send_message(user_input)
        print(f"GM: {response['output']}\n")
        print("=" * 50 + "\n")

        # Mostrar ferramentas usadas
        if response["intermediate_steps"]:
            print("Ferramentas usadas:")
            for step in response["intermediate_steps"]:
                print(f"  - {step[0].tool}: {step[0].tool_input}")
            print("\n" + "=" * 50 + "\n")
