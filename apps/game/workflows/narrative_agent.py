import logging
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("game.narrative_agent")
HYBRID_NARRATIVE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Você é o Game Master de um jogo RPG Fighting Fantasy.
## SUA MISSÃO
Você deve criar uma experiência narrativa RICA e IMERSIVA, mas sempre RESPEITANDO o livro original.
## REGRAS DE OURO
### ✅ LIBERDADE CRIATIVA (Você PODE):
1. **Diálogos Ricos:**
   - NPCs falam com personalidade única
   - Conversas naturais, não são menus de opções
   - Revelam dicas sutis sobre a aventura
   - Reagem ao comportamento do jogador
2. **Descrições Sensoriais:**
   - Descreva cheiros, sons, texturas
   - Crie atmosfera e tensão
   - Adicione detalhes visuais ricos
   - Faça o jogador "sentir" o ambiente
3. **Combate Tático:**
   - Aceite táticas criativas (investidas, esquivas, etc)
   - Descreva golpes de forma cinematográfica
   - Narre consequências físicas dos ataques
   - MAS: mecânica de dados permanece IGUAL
4. **Exploração Livre:**
   - Jogador pode procurar, examinar, cheirar
   - Responda com flavor text rico
   - Se não há nada, diga de forma interessante
### ❌ RESTRIÇÕES RÍGIDAS (Você NÃO PODE):
1. **Itens:**
   - NUNCA invente itens que não estão na whitelist
   - NUNCA permita encontrar itens fora da seção correta
   - Se jogador procura algo inexistente: "Você procura mas não encontra"
2. **Navegação:**
   - NUNCA permita ir para seções não conectadas
   - SEMPRE valide se caminho existe
   - Se caminho bloqueado: explique por que
3. **Progressão:**
   - NUNCA permita pular etapas obrigatórias
   - Se falta chave/item: "A porta está trancada"
   - Respeite sequência linear do livro
4. **Mecânica:**
   - Dados são LEI ABSOLUTA
   - Não altere stats arbitrariamente
   - Combate segue regras Fighting Fantasy
5. **NPCs:**
   - Mantenha personalidade do livro
   - Não traiam motivações originais
   - Não revelem informações que não sabem
## FORMATO DE RESPOSTA
Narre em 2ª pessoa (Você...).
Use linguagem envolvente mas concisa.
Sempre termine indicando opções ou perguntando o que jogador faz.
## CONTEXTO ATUAL
**Personagem:** {character_name}
**Stats:** HABILIDADE {skill} | ENERGIA {stamina}/{initial_stamina} | SORTE {luck} | OURO {gold}
**Inventário:** {inventory}
**Seção Atual:** {current_section}
**Conteúdo da Seção:**
{section_content}
**Ação do Jogador:**
{player_action}
**Histórico Recente:**
{recent_history}
**Flags de Progressão:**
{flags}
## AGORA, NARRE A RESPOSTA:""",
        ),
    ]
)


class RigidStructureValidator:
    def __init__(self, book_class_name: str):
        self.book_class_name = book_class_name

    def validate_navigation(
        self,
        current_section: int,
        target_section: int,
        visited_sections: List[int],
        flags: Dict[str, Any],
    ) -> Dict[str, Any]:
        if target_section < current_section - 10:
            return {
                "valid": False,
                "error_message": "Você não pode voltar tanto na história.",
                "reason": "backward_not_allowed",
            }
        return {"valid": True, "error_message": None, "reason": "ok"}

    def validate_item_pickup(
        self, item_name: str, current_section: int, inventory: List[str]
    ) -> Dict[str, Any]:
        if len(inventory) >= 12:
            return {
                "valid": False,
                "error_message": "Seu inventário está cheio! Solte algo primeiro.",
                "reason": "inventory_full",
            }
        return {"valid": True, "error_message": None, "reason": "ok"}

    def validate_action(
        self,
        player_action: str,
        current_section: int,
        flags: Dict[str, Any],
        in_combat: bool,
    ) -> Dict[str, Any]:
        action_lower = player_action.lower()
        if in_combat:
            combat_keywords = ["atacar", "lutar", "golpe", "fugir", "escapar", "usar"]
            if not any(kw in action_lower for kw in combat_keywords):
                return {
                    "valid": False,
                    "error_message": "Você está em combate! Ataque, fuja ou use um item.",
                    "reason": "must_resolve_combat",
                }
        if "abrir porta" in action_lower and not flags.get("has_key", False):
            if flags.get("door_locked", False):
                return {
                    "valid": False,
                    "error_message": "A porta está trancada. Você precisa encontrar a chave.",
                    "reason": "missing_key",
                }
        return {"valid": True, "error_message": None, "reason": "ok"}


def extract_section_metadata(
    section_content: str, section_number: int
) -> Dict[str, Any]:
    import re

    metadata = {
        "section_number": section_number,
        "exits": [],
        "npcs": [],
        "items": [],
        "combat_required": False,
        "enemy": None,
        "tests": [],
        "keywords": [],
    }
    exit_patterns = [
        r"vá para (\d+)",
        r"seção (\d+)",
        r"para o (\d+)",
        r"volte para (\d+)",
    ]
    for pattern in exit_patterns:
        matches = re.findall(pattern, section_content, re.IGNORECASE)
        metadata["exits"].extend([int(m) for m in matches])
    metadata["exits"] = list(set(metadata["exits"]))
    if any(
        word in section_content.lower()
        for word in ["combate", "lute", "ataque", "habilidade", "energia"]
    ):
        metadata["combat_required"] = True
    if "teste sua sorte" in section_content.lower():
        metadata["tests"].append({"type": "luck"})
    if "teste sua habilidade" in section_content.lower():
        metadata["tests"].append({"type": "skill"})
    content_lower = section_content.lower()
    environment_keywords = {
        "dungeon": ["masmorra", "calabouço", "corredor", "pedra"],
        "forest": ["floresta", "árvores", "mata", "bosque"],
        "tavern": ["taverna", "estalagem", "bebidas"],
        "city": ["cidade", "vila", "rua", "mercado"],
        "cave": ["caverna", "gruta", "escuro"],
    }
    for env_type, keywords in environment_keywords.items():
        if any(kw in content_lower for kw in keywords):
            metadata["keywords"].append(env_type)
    return metadata


def generate_hybrid_narrative(
    player_action: str,
    character_name: str,
    skill: int,
    stamina: int,
    initial_stamina: int,
    luck: int,
    gold: int,
    inventory: List[str],
    current_section: int,
    section_content: str,
    recent_history: str,
    flags: Dict[str, Any],
    book_class_name: str,
    in_combat: bool = False,
) -> str:
    validator = RigidStructureValidator(book_class_name)
    validation = validator.validate_action(
        player_action=player_action,
        current_section=current_section,
        flags=flags,
        in_combat=in_combat,
    )
    if not validation["valid"]:
        return validation["error_message"]
    inventory_str = ", ".join(inventory) if inventory else "Vazio"
    flags_str = str(flags) if flags else "{}"
    from langchain_google_genai import ChatGoogleGenerativeAI
    from django.conf import settings

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.8,
        max_output_tokens=1024,
    )
    chain = HYBRID_NARRATIVE_PROMPT | llm
    response = chain.invoke(
        {
            "character_name": character_name,
            "skill": skill,
            "stamina": stamina,
            "initial_stamina": initial_stamina,
            "luck": luck,
            "gold": gold,
            "inventory": inventory_str,
            "current_section": current_section,
            "section_content": section_content,
            "player_action": player_action,
            "recent_history": recent_history,
            "flags": flags_str,
        }
    )
    return response.content
