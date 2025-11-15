"""
🎯 Tools estruturadas para forçar LLM a retornar JSON correto

Usando LangGraph ToolNode + bind_tools para garantir structured output.
A LLM é FORÇADA a chamar a tool, garantindo schema válido.
"""

from typing import List, Dict, Literal, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class GameOption(BaseModel):
    """Uma opção de ação disponível para o jogador."""

    type: Literal[
        "navigation",      # Mover para outro lugar
        "combat",          # Iniciar combate
        "test_skill",      # Teste de HABILIDADE
        "test_luck",       # Teste de SORTE
        "pickup",          # Pegar item
        "use_item",        # Usar item do inventário
        "talk",            # Conversar com NPC
        "examine",         # Examinar objeto/local
        "exploration"      # Exploração geral
    ] = Field(description="Tipo da ação")

    text: str = Field(
        description="Texto descritivo completo da opção (ex: 'Testar sua HABILIDADE para forçar a porta')"
    )

    target: Optional[str] = Field(
        default=None,
        description="Alvo da ação (nome do item, NPC, local). Obrigatório para pickup, use_item, talk, examine."
    )

    stat: Optional[Literal["HABILIDADE", "SORTE"]] = Field(
        default=None,
        description="Stat testado (HABILIDADE ou SORTE). Obrigatório para test_skill e test_luck."
    )

    section: Optional[int] = Field(
        default=None,
        description="Número da seção de destino para navigation"
    )


class NarrativeOutput(BaseModel):
    """Output estruturado da narrativa."""

    narrative: str = Field(
        description="Texto narrativo em 2ª pessoa, estilo Fighting Fantasy. 2-4 parágrafos descritivos."
    )

    options: List[GameOption] = Field(
        description="Lista de 3-4 opções disponíveis para o jogador. Use bullet points (•) no texto.",
        min_length=2,
        max_length=5
    )


@tool(args_schema=NarrativeOutput)
def provide_game_narrative(narrative: str, options: List[Dict]) -> Dict:
    """
    Fornece a narrativa do jogo e opções estruturadas.

    IMPORTANTE: Esta tool DEVE ser chamada com:
    - narrative: Texto narrativo descritivo (2-4 parágrafos)
    - options: Lista de 3-4 opções com type, text, e campos opcionais

    A LLM DEVE chamar esta tool para retornar a resposta ao jogador.
    """
    # Tool é apenas um schema - o valor retornado é processado externamente
    return {
        "narrative": narrative,
        "options": options
    }


# Lista de tools para bind
NARRATIVE_TOOLS = [provide_game_narrative]
