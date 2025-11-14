"""
🎯 Parser para extrair JSON estruturado das respostas da LLM

A LLM retorna narrativa + JSON com metadados das opções.
Este parser separa a narrativa do JSON.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("game.json_parser")


def extract_narrative_and_options(llm_response: str) -> Tuple[str, List[Dict]]:
    """
    Extrai narrativa e opções estruturadas da resposta da LLM.

    A LLM retorna:
    ```
    [NARRATIVA...]

    ```json
    {
      "options": [...]
    }
    ```
    ```

    Returns:
        (narrativa_limpa, lista_de_opcoes)
    """
    try:
        # Procurar por bloco JSON no final da resposta
        # Padrão: ```json ... ``` ou apenas { "options": [...] }
        json_match = re.search(
            r'```json\s*(\{.*?"options".*?\})\s*```',
            llm_response,
            re.DOTALL | re.IGNORECASE
        )

        if not json_match:
            # Tentar sem markdown code block
            json_match = re.search(
                r'(\{.*?"options".*?\})\s*$',
                llm_response,
                re.DOTALL
            )

        if json_match:
            json_str = json_match.group(1)
            options_data = json.loads(json_str)

            # Extrair opções
            options = options_data.get("options", [])

            # Remover JSON da narrativa
            narrative = llm_response[:json_match.start()].strip()

            logger.info(f"✅ JSON extraído: {len(options)} opções encontradas")
            return narrative, options

        else:
            logger.warning("⚠️ Nenhum JSON encontrado na resposta. Retornando sem opções estruturadas.")
            return llm_response.strip(), []

    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao parsear JSON: {e}")
        return llm_response.strip(), []

    except Exception as e:
        logger.error(f"❌ Erro inesperado ao extrair JSON: {e}")
        return llm_response.strip(), []


def validate_option(option: Dict) -> bool:
    """
    Valida se uma opção tem os campos obrigatórios.

    Campos obrigatórios:
    - type: str (navigation, combat, test_skill, test_luck, etc)
    - text: str (texto descritivo da opção)

    Campos opcionais:
    - target: str (alvo da ação: item, NPC, local)
    - stat: str (HABILIDADE, SORTE)
    """
    required_fields = ["type", "text"]

    for field in required_fields:
        if field not in option:
            logger.warning(f"⚠️ Opção inválida: falta campo '{field}' - {option}")
            return False

    valid_types = [
        "navigation", "combat", "test_skill", "test_luck",
        "pickup", "use_item", "talk", "examine", "exploration"
    ]

    if option["type"] not in valid_types:
        logger.warning(f"⚠️ Tipo de opção inválido: '{option['type']}' - {option}")
        return False

    return True


def filter_valid_options(options: List[Dict]) -> List[Dict]:
    """Filtra apenas opções válidas."""
    return [opt for opt in options if validate_option(opt)]
