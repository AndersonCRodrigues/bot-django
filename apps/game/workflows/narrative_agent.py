"""
Agente Narrativo Híbrido para Fighting Fantasy.

LIBERDADE:
- Diálogos ricos e criativos com NPCs
- Exploração sensorial detalhada
- Combate tático e descritivo
- Interações não previstas no livro

ESTRUTURA RÍGIDA:
- Navegação apenas para seções conectadas
- Itens somente da whitelist do livro
- Progressão linear (não pode pular seções)
- Mecânica de dados imutável
- NPCs fiéis à personalidade do livro

Este agente garante que o jogador tenha LIBERDADE CRIATIVA
dentro de uma ESTRUTURA RÍGIDA do livro original.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("game.narrative_agent")


# ===== PROMPT DO AGENTE NARRATIVO HÍBRIDO =====

HYBRID_NARRATIVE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é o Game Master de um jogo RPG Fighting Fantasy.

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

## AGORA, NARRE A RESPOSTA:"""),
])


# ===== VALIDADOR DE ESTRUTURA RÍGIDA =====

class RigidStructureValidator:
    """
    Valida se ações do jogador respeitam a estrutura do livro.

    SEMPRE valida ANTES de permitir LLM narrar.
    """

    def __init__(self, book_class_name: str):
        self.book_class_name = book_class_name

    def validate_navigation(
        self,
        current_section: int,
        target_section: int,
        visited_sections: List[int],
        flags: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valida se pode navegar para seção alvo.

        Returns:
            {
                "valid": bool,
                "error_message": str | None,
                "reason": str
            }
        """
        # TODO: Buscar exits da seção no Weaviate
        # Por ora, aceita qualquer navegação para frente
        # Em produção: buscar metadata da seção

        # Exemplo de validação:
        # section_data = get_section_metadata(self.book_class_name, current_section)
        # allowed_exits = section_data.get("exits", [])
        #
        # if target_section not in allowed_exits:
        #     return {
        #         "valid": False,
        #         "error_message": f"Você não pode ir diretamente para a seção {target_section} daqui.",
        #         "reason": "path_not_connected"
        #     }

        # Validação simples: não pode voltar muito
        if target_section < current_section - 10:
            return {
                "valid": False,
                "error_message": "Você não pode voltar tanto na história.",
                "reason": "backward_not_allowed"
            }

        return {
            "valid": True,
            "error_message": None,
            "reason": "ok"
        }

    def validate_item_pickup(
        self,
        item_name: str,
        current_section: int,
        inventory: List[str]
    ) -> Dict[str, Any]:
        """
        Valida se item pode ser pego.

        Returns:
            {
                "valid": bool,
                "error_message": str | None,
                "reason": str
            }
        """
        # TODO: Buscar whitelist de itens da seção no Weaviate
        # Por ora, aceita qualquer item

        # Exemplo de validação:
        # section_items = get_section_items(self.book_class_name, current_section)
        # allowed_items = section_items.get("available_items", [])
        #
        # if item_name not in allowed_items:
        #     return {
        #         "valid": False,
        #         "error_message": f"Você não encontra {item_name} aqui.",
        #         "reason": "item_not_in_section"
        #     }

        # Validação de inventário cheio
        if len(inventory) >= 12:
            return {
                "valid": False,
                "error_message": "Seu inventário está cheio! Solte algo primeiro.",
                "reason": "inventory_full"
            }

        return {
            "valid": True,
            "error_message": None,
            "reason": "ok"
        }

    def validate_action(
        self,
        player_action: str,
        current_section: int,
        flags: Dict[str, Any],
        in_combat: bool
    ) -> Dict[str, Any]:
        """
        Validação geral de ação.

        Returns:
            {
                "valid": bool,
                "error_message": str | None,
                "reason": str
            }
        """
        action_lower = player_action.lower()

        # Em combate: só pode atacar, fugir ou usar item
        if in_combat:
            combat_keywords = ["atacar", "lutar", "golpe", "fugir", "escapar", "usar"]
            if not any(kw in action_lower for kw in combat_keywords):
                return {
                    "valid": False,
                    "error_message": "Você está em combate! Ataque, fuja ou use um item.",
                    "reason": "must_resolve_combat"
                }

        # Validações específicas de flags
        # Exemplo: porta trancada sem chave
        if "abrir porta" in action_lower and not flags.get("has_key", False):
            if flags.get("door_locked", False):
                return {
                    "valid": False,
                    "error_message": "A porta está trancada. Você precisa encontrar a chave.",
                    "reason": "missing_key"
                }

        return {
            "valid": True,
            "error_message": None,
            "reason": "ok"
        }


# ===== EXTRATOR DE METADADOS DE SEÇÃO =====

def extract_section_metadata(section_content: str, section_number: int) -> Dict[str, Any]:
    """
    Extrai metadados de uma seção do livro Fighting Fantasy.

    Args:
        section_content: Texto da seção
        section_number: Número da seção

    Returns:
        {
            "exits": List[int],  # Seções conectadas
            "npcs": List[str],   # NPCs presentes
            "items": List[str],  # Itens disponíveis
            "combat_required": bool,
            "enemy": Dict | None,
            "tests": List[Dict],
            "keywords": List[str]  # Para detecção de ambiente
        }
    """
    import re

    metadata = {
        "section_number": section_number,
        "exits": [],
        "npcs": [],
        "items": [],
        "combat_required": False,
        "enemy": None,
        "tests": [],
        "keywords": []
    }

    # Extrair exits (padrão: "vá para 23" ou "seção 45")
    exit_patterns = [
        r'vá para (\d+)',
        r'seção (\d+)',
        r'para o (\d+)',
        r'volte para (\d+)'
    ]

    for pattern in exit_patterns:
        matches = re.findall(pattern, section_content, re.IGNORECASE)
        metadata["exits"].extend([int(m) for m in matches])

    # Remove duplicatas
    metadata["exits"] = list(set(metadata["exits"]))

    # Detectar combate
    if any(word in section_content.lower() for word in ["combate", "lute", "ataque", "habilidade", "energia"]):
        metadata["combat_required"] = True

    # Detectar testes
    if "teste sua sorte" in section_content.lower():
        metadata["tests"].append({"type": "luck"})

    if "teste sua habilidade" in section_content.lower():
        metadata["tests"].append({"type": "skill"})

    # Keywords de ambiente
    content_lower = section_content.lower()
    environment_keywords = {
        "dungeon": ["masmorra", "calabouço", "corredor", "pedra"],
        "forest": ["floresta", "árvores", "mata", "bosque"],
        "tavern": ["taverna", "estalagem", "bebidas"],
        "city": ["cidade", "vila", "rua", "mercado"],
        "cave": ["caverna", "gruta", "escuro"]
    }

    for env_type, keywords in environment_keywords.items():
        if any(kw in content_lower for kw in keywords):
            metadata["keywords"].append(env_type)

    return metadata


# ===== FUNÇÃO PRINCIPAL: GERAR NARRATIVA HÍBRIDA =====

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
    in_combat: bool = False
) -> str:
    """
    Gera narrativa usando o agente híbrido.

    Esta função:
    1. Valida estrutura rígida
    2. Se válido, gera narrativa criativa
    3. Retorna narrativa + metadata de áudio/achievements

    Args:
        player_action: Ação do jogador
        character_name: Nome do personagem
        skill: HABILIDADE
        stamina: ENERGIA
        initial_stamina: ENERGIA inicial
        luck: SORTE
        gold: Ouro
        inventory: Lista de itens
        current_section: Seção atual
        section_content: Conteúdo da seção
        recent_history: Histórico recente
        flags: Flags de progressão
        book_class_name: Nome da classe Weaviate
        in_combat: Se está em combate

    Returns:
        Texto narrativo
    """
    # 1. Validar ação
    validator = RigidStructureValidator(book_class_name)

    validation = validator.validate_action(
        player_action=player_action,
        current_section=current_section,
        flags=flags,
        in_combat=in_combat
    )

    if not validation["valid"]:
        return validation["error_message"]

    # 2. Preparar contexto
    inventory_str = ", ".join(inventory) if inventory else "Vazio"
    flags_str = str(flags) if flags else "{}"

    # 3. Gerar narrativa via LLM
    from langchain_google_genai import ChatGoogleGenerativeAI
    from django.conf import settings

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.8,  # Alta criatividade
        max_output_tokens=1024
    )

    chain = HYBRID_NARRATIVE_PROMPT | llm

    response = chain.invoke({
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
        "flags": flags_str
    })

    return response.content
