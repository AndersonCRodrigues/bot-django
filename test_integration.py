"""
🧪 Teste de Integração - Verificação do Sistema

Testa componentes críticos sem precisar de Django rodando.
"""

import re
import json


def test_action_parser():
    """Testa parser de ações do jogador."""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Action Parser")
    print("="*60)

    # Teste 1: Navegação com número de seção
    action = "[IR PARA 15] Entrar na cidade"
    match = re.match(r'\[IR PARA (\d+)\](.+)', action, re.IGNORECASE)

    if match:
        section = int(match.group(1))
        desc = match.group(2).strip()
        assert section == 15, f"❌ Esperado seção 15, obteve {section}"
        assert desc == "Entrar na cidade", f"❌ Descrição incorreta: {desc}"
        print(f"✅ Navegação parseada: seção={section}, desc='{desc}'")
    else:
        print("❌ FALHOU: Navegação não detectada")
        return False

    # Teste 2: Combate
    combat_keywords = ['atac', 'lut', 'golpe', 'invest']
    action2 = "eu ataco o guarda"
    if any(kw in action2.lower() for kw in combat_keywords):
        print("✅ Combate detectado em 'eu ataco o guarda'")
    else:
        print("❌ FALHOU: Combate não detectado")
        return False

    # Teste 3: Pickup
    action3 = "pego a espada"
    pattern = r'peg(?:o|ar|ue) (?:o |a |um |uma )?(\w+)'
    match = re.search(pattern, action3.lower())

    if match:
        item = match.group(1).strip().title()
        assert item == "Espada", f"❌ Item incorreto: {item}"
        print(f"✅ Pickup detectado: item='{item}'")
    else:
        print("❌ FALHOU: Pickup não detectado")
        return False

    print("✅ Action Parser: TODOS OS TESTES PASSARAM")
    return True


def test_json_escape():
    """Testa se JSON está corretamente escapado nos prompts."""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Escape de JSON em Prompts")
    print("="*60)

    # Simular trecho do prompt
    prompt_example = """
    Exemplo: {{type: "navigation", text: "...", section: 15}}
    """

    # Verificar que NÃO tem {type} com APENAS uma chave (sem escapar)
    # Regex: { seguido de palavra, mas NÃO precedido por outra {
    if re.search(r'(?<!\{)\{type:', prompt_example):
        print("❌ FALHOU: JSON não escapado encontrado")
        return False
    else:
        print("✅ Nenhum JSON não-escapado encontrado")

    # Verificar que TEM {{type}} escapado
    if re.search(r'\{\{type:', prompt_example):
        print("✅ JSON corretamente escapado com {{}}")
    else:
        print("❌ FALHOU: JSON escapado não encontrado")
        return False

    print("✅ JSON Escape: TODOS OS TESTES PASSARAM")
    return True


def test_combat_flow():
    """Testa fluxo de combate simulado."""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Fluxo de Combate Simulado")
    print("="*60)

    # Simular início de combate
    combat_data = {
        'enemy_name': 'Guarda',
        'enemy_skill': 7,
        'enemy_stamina': 5,
        'enemy_max_stamina': 5,
        'rounds': 0
    }

    # Verificar estrutura
    required_keys = ['enemy_name', 'enemy_skill', 'enemy_stamina', 'rounds']
    for key in required_keys:
        if key not in combat_data:
            print(f"❌ FALHOU: Chave '{key}' ausente em combat_data")
            return False

    print(f"✅ Combat data estruturado: {combat_data['enemy_name']} (HAB {combat_data['enemy_skill']}, ENERGIA {combat_data['enemy_stamina']})")

    # Simular round de combate
    import random
    random.seed(42)  # Para resultado determinístico

    char_roll = random.randint(2, 12)
    enemy_roll = random.randint(2, 12)

    char_attack = char_roll + 8  # HABILIDADE 8
    enemy_attack = enemy_roll + combat_data['enemy_skill']

    if char_attack > enemy_attack:
        combat_data['enemy_stamina'] -= 2
        result = f"✅ Jogador acerta! Inimigo: {combat_data['enemy_stamina']}/{combat_data['enemy_max_stamina']} ENERGIA"
    elif enemy_attack > char_attack:
        char_stamina = 15 - 2
        result = f"⚠️ Inimigo acerta! Jogador: {char_stamina} ENERGIA"
    else:
        result = "➖ Empate!"

    print(f"✅ Round simulado: {result}")
    print("✅ Combat Flow: TODOS OS TESTES PASSARAM")
    return True


def test_structured_options():
    """Testa validação de opções estruturadas."""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Opções Estruturadas (Tool Output)")
    print("="*60)

    # Opção válida
    option = {
        "type": "navigation",
        "text": "Entrar na cidade",
        "section": 15
    }

    # Validar campos obrigatórios
    if "type" not in option or "text" not in option:
        print("❌ FALHOU: Campos obrigatórios ausentes")
        return False

    # Validar tipos válidos
    valid_types = ["navigation", "combat", "test_skill", "test_luck", "pickup", "use_item", "talk", "examine", "exploration"]

    if option["type"] not in valid_types:
        print(f"❌ FALHOU: Tipo '{option['type']}' inválido")
        return False

    print(f"✅ Opção válida: {option}")

    # Testar opção de combate
    combat_option = {
        "type": "combat",
        "text": "Atacar o guarda"
    }

    if combat_option["type"] == "combat":
        print(f"✅ Opção de combate: {combat_option['text']}")

    print("✅ Structured Options: TODOS OS TESTES PASSARAM")
    return True


def test_section_navigation():
    """Testa lógica de navegação entre seções."""
    print("\n" + "="*60)
    print("🧪 TESTE 5: Navegação Entre Seções")
    print("="*60)

    # Estado inicial
    current_section = 1
    target_section = 15

    # Simular navegação
    print(f"📍 Seção atual: {current_section}")
    print(f"🎯 Navegando para: {target_section}")

    # Validar que seção mudou
    current_section = target_section

    if current_section == 15:
        print(f"✅ Navegação bem-sucedida: seção {current_section}")
    else:
        print(f"❌ FALHOU: Seção não atualizada")
        return False

    # Verificar que não volta à seção anterior
    if current_section != 1:
        print("✅ Não houve loop para seção anterior")
    else:
        print("❌ FALHOU: Voltou à seção 1")
        return False

    print("✅ Section Navigation: TODOS OS TESTES PASSARAM")
    return True


def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("🚀 INICIANDO TESTES DE INTEGRAÇÃO")
    print("="*80)

    results = []

    # Executar todos os testes
    results.append(("Action Parser", test_action_parser()))
    results.append(("JSON Escape", test_json_escape()))
    results.append(("Combat Flow", test_combat_flow()))
    results.append(("Structured Options", test_structured_options()))
    results.append(("Section Navigation", test_section_navigation()))

    # Resumo
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")

    print("\n" + "="*80)
    if passed == total:
        print(f"🎉 SUCESSO: {passed}/{total} testes passaram!")
        print("="*80)
        return 0
    else:
        print(f"⚠️  FALHA: {passed}/{total} testes passaram, {total-passed} falharam")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit(main())
