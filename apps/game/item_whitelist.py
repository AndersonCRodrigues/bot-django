"""
Whitelist de itens permitidos por seção em cada livro.

ANTI-ALUCINAÇÃO: LLM só pode dar itens que estão nesta whitelist.
Se jogador "procurar" algo que não está na seção, não encontra.

Estrutura:
{
    "NomeLivro": {
        numero_secao: ["ITEM_1", "ITEM_2", ...],
        ...
    }
}

IMPORTANTE:
- Itens em MAIÚSCULAS com underscore
- Apenas itens realmente presentes no livro original
- Se seção não tem itens especiais, lista vazia []
"""

# Whitelist de itens por livro e seção
BOOK_ITEM_WHITELISTS = {
    # O Feiticeiro da Montanha de Fogo (exemplo)
    "WarriorOfBlood": {
        # Seção 1: Início da aventura
        1: ["ESPADA", "MOCHILA", "LANTERNA", "PROVISÕES"],

        # Seção 5: Taverna do Dragão Dourado
        5: ["CHAVE_BRONZE", "MOEDAS_OURO", "CERVEJA"],

        # Seção 12: Corredor dos Espelhos
        12: ["ESPELHO_MÁGICO", "POÇÃO_INVISIBILIDADE"],

        # Seção 18: Câmara do Tesouro
        18: ["GEMA_VERMELHA", "COROA_ANTIGA", "PERGAMINHO"],

        # Seção 25: Armário do Alquimista
        25: ["POÇÃO_CURA", "ERVAS_RARAS", "FRASCO_VAZIO"],

        # Seção 33: Quarto do Guarda
        33: ["CHAVE_PRATA", "ARMADURA_LEVE", "TOCHA"],

        # Seção 42: Biblioteca Secreta
        42: ["LIVRO_FEITIÇOS", "MAPA_ANTIGO", "PENA_DOURADA"],

        # Seção 50: Baú do Tesouro
        50: ["ANEL_PODER", "COLAR_PROTEÇÃO", "BOLSA_MOEDAS"],

        # Seção 67: Sala de Armas
        67: ["ADAGA_ÉLFICA", "ARCO_LONGO", "FLECHAS"],

        # Seção 75: Altar Misterioso
        75: ["CÁLICE_SAGRADO", "PEDRA_RÚNICA", "AMULETO"],

        # Seção 88: Caverna do Eremita
        88: ["CAJADO_MADEIRA", "POÇÃO_FORÇA", "MANTO_VERDE"],

        # Seção 100: Ponte dos Goblins
        100: ["CORDA", "GANCHO", "PICARETA"],

        # Seção 125: Torre do Mago
        125: ["VARINHA_MÁGICA", "CRISTAL_AZUL", "GRIMÓRIO"],

        # Seção 150: Forja Antiga
        150: ["MARTELO_ANÃO", "BIGORNA_FERRO", "CARVÃO"],

        # Seção 175: Jardim Encantado
        175: ["FLOR_DOURADA", "SEMENTE_MÁGICA", "REGADOR"],

        # Seção 200: Laboratório
        200: ["ALAMBIQUE", "SUBSTÂNCIA_VERDE", "PROVETA"],

        # Seção 225: Cofre do Rei
        225: ["COROA_REI", "CETRO_OURO", "JOIA_REAL"],

        # Seção 250: Cozinha do Castelo
        250: ["FACA_COZINHA", "PÃO_FRESCO", "VINHO"],

        # Seção 275: Estábulo
        275: ["SELA", "RÉDEAS", "ESCOVA"],

        # Seção 300: Sala do Trono
        300: ["TAPETE_REAL", "ESTANDARTE", "BRASÃO"],

        # Adicionar mais seções conforme necessário
        # A maioria das seções não tem itens especiais
    }
}

# Itens de base que o personagem SEMPRE tem (não podem ser removidos)
BASE_ITEMS = ["ESPADA", "MOCHILA", "LANTERNA"]

# Itens globais que podem aparecer em qualquer lugar (moedas, provisões básicas)
GLOBAL_ITEMS = ["MOEDAS_OURO", "PROVISÕES", "TOCHA", "CORDA"]


def get_allowed_items(book_class_name: str, section_number: int) -> list:
    """
    Retorna lista de itens permitidos para uma seção específica.

    Args:
        book_class_name: Nome da classe do livro no Weaviate
        section_number: Número da seção (1-400)

    Returns:
        Lista de itens permitidos (strings em MAIÚSCULAS)
    """
    book_whitelist = BOOK_ITEM_WHITELISTS.get(book_class_name, {})
    section_items = book_whitelist.get(section_number, [])

    # Combinar itens da seção + itens globais
    allowed = section_items + GLOBAL_ITEMS

    return list(set(allowed))  # Remove duplicatas


def validate_item_pickup(
    item_name: str,
    section_number: int,
    book_class_name: str
) -> dict:
    """
    Valida se um item pode ser pego na seção atual.

    Args:
        item_name: Nome do item (será normalizado)
        section_number: Seção atual
        book_class_name: Livro atual

    Returns:
        {
            'valid': bool,
            'item_normalized': str,
            'reason': str,
            'allowed_items': list
        }
    """
    # Normalizar item
    item_normalized = item_name.upper().replace(" ", "_")

    # Verificar se é item de base (sempre permitido)
    if item_normalized in BASE_ITEMS:
        return {
            'valid': True,
            'item_normalized': item_normalized,
            'reason': 'base_item',
            'allowed_items': []
        }

    # Buscar itens permitidos
    allowed_items = get_allowed_items(book_class_name, section_number)

    # Validar
    if item_normalized in allowed_items:
        return {
            'valid': True,
            'item_normalized': item_normalized,
            'reason': 'whitelisted',
            'allowed_items': allowed_items
        }
    else:
        return {
            'valid': False,
            'item_normalized': item_normalized,
            'reason': 'not_in_whitelist',
            'allowed_items': allowed_items,
            'error_message': (
                f"Você procura por {item_name}, mas não encontra nada parecido aqui. "
                f"Talvez esteja em outro lugar..."
            )
        }


def add_item_to_whitelist(
    book_class_name: str,
    section_number: int,
    item_name: str
):
    """
    Adiciona um item à whitelist (uso administrativo).

    Args:
        book_class_name: Nome do livro
        section_number: Seção
        item_name: Nome do item
    """
    if book_class_name not in BOOK_ITEM_WHITELISTS:
        BOOK_ITEM_WHITELISTS[book_class_name] = {}

    if section_number not in BOOK_ITEM_WHITELISTS[book_class_name]:
        BOOK_ITEM_WHITELISTS[book_class_name][section_number] = []

    item_normalized = item_name.upper().replace(" ", "_")

    if item_normalized not in BOOK_ITEM_WHITELISTS[book_class_name][section_number]:
        BOOK_ITEM_WHITELISTS[book_class_name][section_number].append(item_normalized)


def get_book_statistics(book_class_name: str) -> dict:
    """
    Retorna estatísticas da whitelist de um livro.

    Returns:
        {
            'total_sections_with_items': int,
            'total_unique_items': int,
            'sections': list
        }
    """
    book_data = BOOK_ITEM_WHITELISTS.get(book_class_name, {})

    all_items = set()
    for items in book_data.values():
        all_items.update(items)

    return {
        'total_sections_with_items': len(book_data),
        'total_unique_items': len(all_items),
        'sections': sorted(book_data.keys())
    }
