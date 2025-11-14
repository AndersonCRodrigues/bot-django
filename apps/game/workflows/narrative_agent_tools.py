"""
🎯 Agent Narrativo com ToolNode - CRÍTICO!

Sistema que transforma a LLM em um verdadeiro agente ReAct
que pode chamar ferramentas diretamente.

Resolve o problema #1 da análise: LLM não tinha acesso direto a tools!
"""

import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings

logger = logging.getLogger("game.narrative_agent_tools")


# ========================================
# 🛠️ TOOLS PARA O AGENTE
# ========================================

@tool
def update_stat(character_id: str, stat_name: str, change: int) -> dict:
    """
    Atualiza um atributo do personagem (HABILIDADE, ENERGIA, SORTE, OURO).

    Args:
        character_id: ID do personagem
        stat_name: Nome do atributo (skill, stamina, luck, gold)
        change: Valor da mudança (pode ser positivo ou negativo)

    Returns:
        dict com sucesso e novo valor

    Exemplos:
        - Personagem perde 2 de ENERGIA: update_stat(char_id, "stamina", -2)
        - Personagem ganha 10 de OURO: update_stat(char_id, "gold", 10)
        - Personagem perde 1 de SORTE: update_stat(char_id, "luck", -1)
    """
    from apps.characters.models import Character
    from bson import ObjectId

    try:
        collection = Character.get_collection()
        character_doc = collection.find_one({"_id": ObjectId(character_id)})

        if not character_doc:
            return {"success": False, "error": "Personagem não encontrado"}

        stat_name = stat_name.lower()
        if stat_name not in ["skill", "stamina", "luck", "gold", "provisions"]:
            return {"success": False, "error": f"Stat inválido: {stat_name}"}

        old_value = character_doc.get(stat_name, 0)
        new_value = old_value + change

        # Limites mínimos
        if stat_name in ["stamina", "skill", "luck"]:
            new_value = max(0, new_value)

        collection.update_one(
            {"_id": ObjectId(character_id)},
            {"$set": {stat_name: new_value}}
        )

        logger.info(
            f"[update_stat] {stat_name.upper()}: {old_value} → {new_value} "
            f"(change: {change:+d})"
        )

        return {
            "success": True,
            "stat": stat_name,
            "old_value": old_value,
            "new_value": new_value,
            "change": change
        }

    except Exception as e:
        logger.error(f"[update_stat] Erro: {e}")
        return {"success": False, "error": str(e)}


@tool
def add_item_to_inventory(character_id: str, item_name: str, session_id: str) -> dict:
    """
    Adiciona item ao inventário do personagem.

    Args:
        character_id: ID do personagem
        item_name: Nome do item (SEMPRE EM MAIÚSCULAS)
        session_id: ID da sessão

    Returns:
        dict com sucesso e inventário atualizado

    IMPORTANTE: Item deve estar na whitelist da seção atual!
    """
    from apps.game.models import GameSession
    from apps.characters.models import Character
    from bson import ObjectId

    try:
        session = GameSession.find_by_id(session_id, None)
        if not session:
            return {"success": False, "error": "Sessão não encontrada"}

        # Validar whitelist
        from apps.game.item_whitelist import validate_item_pickup
        validation = validate_item_pickup(
            item_name,
            session.current_section,
            session.get_book_class_name()
        )

        if not validation["valid"]:
            logger.warning(
                f"[add_item_to_inventory] Item '{item_name}' bloqueado pela whitelist"
            )
            return {
                "success": False,
                "error": validation["error_message"],
                "reason": "not_in_whitelist"
            }

        item_normalized = validation["item_normalized"]

        # Adicionar ao inventário
        if item_normalized not in session.inventory:
            session.inventory.append(item_normalized)
            session.save()

            logger.info(f"[add_item_to_inventory] Item adicionado: {item_normalized}")

            return {
                "success": True,
                "item": item_normalized,
                "inventory": session.inventory
            }
        else:
            return {
                "success": False,
                "error": f"Você já tem {item_normalized}"
            }

    except Exception as e:
        logger.error(f"[add_item_to_inventory] Erro: {e}")
        return {"success": False, "error": str(e)}


@tool
def remove_item_from_inventory(character_id: str, item_name: str, session_id: str) -> dict:
    """
    Remove item do inventário.

    Args:
        character_id: ID do personagem
        item_name: Nome do item
        session_id: ID da sessão

    Returns:
        dict com sucesso
    """
    from apps.game.models import GameSession

    try:
        session = GameSession.find_by_id(session_id, None)
        if not session:
            return {"success": False, "error": "Sessão não encontrada"}

        item_upper = item_name.upper()

        if item_upper in session.inventory:
            session.inventory.remove(item_upper)
            session.save()

            logger.info(f"[remove_item_from_inventory] Item removido: {item_upper}")

            return {
                "success": True,
                "item": item_upper,
                "inventory": session.inventory
            }
        else:
            return {
                "success": False,
                "error": f"Você não tem {item_upper}"
            }

    except Exception as e:
        logger.error(f"[remove_item_from_inventory] Erro: {e}")
        return {"success": False, "error": str(e)}


@tool
def check_inventory_for_item(session_id: str, item_name: str) -> dict:
    """
    Verifica se personagem possui um item.

    Args:
        session_id: ID da sessão
        item_name: Nome do item

    Returns:
        dict com has_item (bool)
    """
    from apps.game.models import GameSession

    try:
        session = GameSession.find_by_id(session_id, None)
        if not session:
            return {"success": False, "error": "Sessão não encontrada"}

        item_upper = item_name.upper()
        has_item = item_upper in session.inventory

        return {
            "success": True,
            "has_item": has_item,
            "item": item_upper
        }

    except Exception as e:
        logger.error(f"[check_inventory_for_item] Erro: {e}")
        return {"success": False, "error": str(e)}


@tool
def validate_navigation_to_section(current_section: int, target_section: int, book_class_name: str) -> dict:
    """
    Valida se pode navegar de current_section para target_section.

    Args:
        current_section: Seção atual
        target_section: Seção de destino
        book_class_name: Nome da classe do livro

    Returns:
        dict com valid (bool) e reason (str)

    IMPORTANTE: Use auto_extracted_exits da state para validar!
    """
    # Esta ferramenta será usada pelo agente para validar navegação
    # Os exits já foram extraídos pelo RAG
    logger.info(
        f"[validate_navigation] Validando: {current_section} → {target_section}"
    )

    return {
        "success": True,
        "message": "Validação deve usar auto_extracted_exits da state"
    }


@tool
def set_flag(session_id: str, flag_name: str, flag_value: Any) -> dict:
    """
    Define uma flag de progressão (porta aberta, boss derrotado, etc).

    Args:
        session_id: ID da sessão
        flag_name: Nome da flag
        flag_value: Valor da flag (bool, str, int, etc)

    Returns:
        dict com sucesso
    """
    from apps.game.models import GameSession

    try:
        session = GameSession.find_by_id(session_id, None)
        if not session:
            return {"success": False, "error": "Sessão não encontrada"}

        session.flags[flag_name] = flag_value
        session.save()

        logger.info(f"[set_flag] Flag definida: {flag_name} = {flag_value}")

        return {
            "success": True,
            "flag_name": flag_name,
            "flag_value": flag_value
        }

    except Exception as e:
        logger.error(f"[set_flag] Erro: {e}")
        return {"success": False, "error": str(e)}


# ========================================
# 🤖 PROMPT DO AGENTE
# ========================================

AGENT_NARRATIVE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é o Game Master de um jogo RPG Fighting Fantasy.

## FERRAMENTAS DISPONÍVEIS

Você tem acesso a ferramentas para:
- **update_stat**: Atualizar HABILIDADE, ENERGIA, SORTE, OURO
- **add_item_to_inventory**: Adicionar item (validado pela whitelist)
- **remove_item_from_inventory**: Remover item usado/perdido
- **check_inventory_for_item**: Verificar se personagem tem item
- **set_flag**: Marcar progressão (porta aberta, chave usada, etc)

## QUANDO USAR FERRAMENTAS

✅ USE ferramentas quando:
- Personagem perde/ganha ENERGIA em combate/armadilha
- Personagem encontra/pega item mencionado na seção
- Personagem usa/perde item
- Personagem ganha OURO
- Personagem abre porta/derrota boss (set_flag)
- Testa SORTE (perde 1 ponto)

❌ NÃO USE ferramentas para:
- Narração pura sem mudanças mecânicas
- Conversas com NPCs sem recompensas
- Descrições de ambiente

## REGRAS RÍGIDAS

1. **Itens**: APENAS itens da whitelist da seção podem ser adicionados
2. **Navegação**: APENAS seções em auto_extracted_exits são permitidas
3. **Stats**: NUNCA altere valores arbitrariamente
4. **Combate**: Use mecânica Fighting Fantasy (2d6 + HABILIDADE)

## CONTEXTO ATUAL

**Personagem**: {character_name}
**Stats**: HABILIDADE {skill} | ENERGIA {stamina}/{initial_stamina} | SORTE {luck} | OURO {gold}
**Inventário**: {inventory}

**Seção Atual**: {current_section}
**Conteúdo da Seção**:
{section_content}

**Exits Permitidos**: {auto_extracted_exits}
**Flags Detectados**: {auto_extracted_flags}
**NPCs**: {auto_extracted_npcs}
**Combate**: {auto_extracted_combat}

**Ação do Jogador**: {player_action}

**Histórico Recente**:
{recent_history}

## SUA TAREFA

Narre a resposta à ação do jogador:
1. Se a ação causa mudanças mecânicas, USE as ferramentas
2. Narre em 2ª pessoa (Você...)
3. Seja descritivo mas conciso (2-4 parágrafos)
4. Termine indicando opções ou perguntando o que jogador faz
5. NUNCA mencione números de seções - use descrições narrativas

AGORA, NARRE A RESPOSTA:"""),
])


# ========================================
# 🎯 GET TOOLS LIST
# ========================================

def get_narrative_agent_tools() -> List:
    """Retorna lista de tools para o agente narrativo."""
    return [
        update_stat,
        add_item_to_inventory,
        remove_item_from_inventory,
        check_inventory_for_item,
        validate_navigation_to_section,
        set_flag,
    ]
