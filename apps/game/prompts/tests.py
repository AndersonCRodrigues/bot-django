"""
Testes para o sistema de prompts do Game Master.
"""

import pytest
from apps.game.prompts import get_game_master_prompt


class TestGameMasterPrompt:
    """Testes para o prompt do Game Master."""

    def test_prompt_generation(self):
        """Testa se o prompt é gerado corretamente."""
        character_id = "507f1f77bcf86cd799439011"
        adventure_name = "FeiticeiroDaMontanhaFogo"

        prompt = get_game_master_prompt(
            character_id=character_id, adventure_name=adventure_name
        )

        # Verificar se o prompt contém os IDs corretos
        assert character_id in prompt
        assert adventure_name in prompt

        # Verificar se contém seções principais
        assert "PERFIL E DIRETRIZ PRIMÁRIA" in prompt
        assert "Princípios de Operação Essenciais" in prompt
        assert "Ferramentas Disponíveis" in prompt
        assert "Mecânicas de Jogo" in prompt
        assert "Estrutura Narrativa Digital" in prompt

    def test_prompt_includes_tool_descriptions(self):
        """Testa se o prompt inclui descrições das ferramentas."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        # Verificar ferramentas de personagem
        assert "get_character_state" in prompt
        assert "update_character_stats" in prompt

        # Verificar ferramentas de inventário
        assert "add_item" in prompt
        assert "remove_item" in prompt
        assert "check_item" in prompt
        assert "use_item" in prompt

        # Verificar ferramentas de dados
        assert "roll_dice" in prompt
        assert "check_luck" in prompt
        assert "check_skill" in prompt

        # Verificar ferramentas de combate
        assert "start_combat" in prompt
        assert "combat_round" in prompt

        # Verificar ferramentas de navegação
        assert "get_current_section" in prompt
        assert "try_move_to" in prompt

    def test_prompt_includes_fighting_fantasy_rules(self):
        """Testa se o prompt inclui as regras do Fighting Fantasy."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        # Verificar regras de combate
        assert "RODADA DE COMBATE" in prompt or "Combate" in prompt
        assert "2d6" in prompt

        # Verificar regras de Teste de Sorte
        assert "Teste de Sorte" in prompt
        assert "SUCESSO" in prompt
        assert "FALHA" in prompt

        # Verificar stats
        assert "skill" in prompt.lower() or "habilidade" in prompt.lower()
        assert "stamina" in prompt.lower() or "energia" in prompt.lower()
        assert "luck" in prompt.lower() or "sorte" in prompt.lower()

    def test_prompt_emphasizes_tool_usage(self):
        """Testa se o prompt enfatiza o uso obrigatório de ferramentas."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        # Verificar ênfase em usar ferramentas
        assert "ferramenta" in prompt.lower() or "tool" in prompt.lower()
        assert "NUNCA" in prompt or "nunca" in prompt
        assert "SEMPRE" in prompt or "sempre" in prompt

    def test_prompt_prohibits_technical_language(self):
        """Testa se o prompt proíbe linguagem técnica na narrativa."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        # Verificar proibições
        assert "PROIBIDO" in prompt or "Proibido" in prompt
        assert "imersiv" in prompt.lower()
        assert "narrativa" in prompt.lower()

    def test_prompt_includes_manual_combat_system(self):
        """Testa se o prompt inclui o sistema de combate manual."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        # Verificar menção ao combate manual
        assert "manual" in prompt.lower() or "MANUAL" in prompt
        assert "[ROLE 2d6]" in prompt or "ROLE" in prompt

    def test_prompt_includes_state_validation(self):
        """Testa se o prompt enfatiza validação de estado."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        # Verificar ênfase em validação
        assert "validar" in prompt.lower() or "verificar" in prompt.lower()
        assert "get_character_state" in prompt

    def test_prompt_format_is_string(self):
        """Testa se o prompt retorna uma string."""
        prompt = get_game_master_prompt(
            character_id="test_id", adventure_name="test_adventure"
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Deve ser um prompt extenso

    def test_different_ids_generate_different_prompts(self):
        """Testa se IDs diferentes geram prompts diferentes."""
        prompt1 = get_game_master_prompt(
            character_id="id1", adventure_name="adventure1"
        )
        prompt2 = get_game_master_prompt(
            character_id="id2", adventure_name="adventure2"
        )

        # Prompts devem ser diferentes devido aos IDs
        assert "id1" in prompt1
        assert "id2" in prompt2
        assert "adventure1" in prompt1
        assert "adventure2" in prompt2


class TestPromptIntegrationConcepts:
    """
    Testes conceituais para validar a integração do prompt.
    (Não executam o agente real, apenas validam a estrutura)
    """

    def test_prompt_provides_character_context(self):
        """Testa se o prompt fornece contexto do personagem."""
        character_id = "abc123"
        adventure_name = "TestAdventure"

        prompt = get_game_master_prompt(
            character_id=character_id, adventure_name=adventure_name
        )

        # O prompt deve instruir o agente a usar esses valores
        assert f'character_id="{character_id}"' in prompt or character_id in prompt
        assert (
            f'adventure_name="{adventure_name}"' in prompt or adventure_name in prompt
        )

    def test_prompt_explains_tool_return_values(self):
        """Testa se o prompt explica os valores de retorno das ferramentas."""
        prompt = get_game_master_prompt(
            character_id="test", adventure_name="test"
        )

        # Deve explicar estrutura de retorno
        assert "dict" in prompt.lower() or "Dict" in prompt
        assert "success" in prompt.lower()
        assert "return" in prompt.lower() or "retorna" in prompt.lower()

    def test_prompt_includes_usage_examples(self):
        """Testa se o prompt inclui exemplos de uso."""
        prompt = get_game_master_prompt(
            character_id="test", adventure_name="test"
        )

        # Deve incluir exemplos
        assert "exemplo" in prompt.lower() or "example" in prompt.lower()
        assert "```python" in prompt.lower() or "```" in prompt

    def test_prompt_includes_checklist(self):
        """Testa se o prompt inclui checklist de consistência."""
        prompt = get_game_master_prompt(
            character_id="test", adventure_name="test"
        )

        # Deve incluir checklist
        assert "checklist" in prompt.lower() or "verificar" in prompt.lower()


# ========== Testes de Integração (opcional, requer setup completo) ==========


@pytest.mark.integration
class TestGameMasterAgentIntegration:
    """
    Testes de integração que requerem Django setup completo.
    Execute com: pytest -m integration
    """

    @pytest.fixture
    def mock_character_id(self, db):
        """Fixture para criar um personagem de teste."""
        from apps.characters.models import Character

        character = Character.create(
            name="Test Hero",
            skill=10,
            stamina=20,
            luck=9,
            gold=10,
            provisions=5,
            equipment=["ESPADA", "ESCUDO"],
        )
        return str(character["_id"])

    def test_agent_creation(self, mock_character_id):
        """Testa criação do agente com prompt."""
        from apps.game.prompts.example_usage import GameMasterAgent

        agent = GameMasterAgent(
            character_id=mock_character_id,
            adventure_name="TestAdventure",
        )

        assert agent is not None
        assert agent.character_id == mock_character_id
        assert agent.adventure_name == "TestAdventure"
        assert len(agent.tools) > 0

    def test_agent_message_handling(self, mock_character_id):
        """Testa envio de mensagem ao agente."""
        from apps.game.prompts.example_usage import GameMasterAgent

        agent = GameMasterAgent(
            character_id=mock_character_id,
            adventure_name="TestAdventure",
        )

        # Enviar mensagem simples
        response = agent.send_message("Olá, Game Master!")

        assert "output" in response
        assert isinstance(response["output"], str)
        assert len(response["chat_history"]) > 0
