# 🔍 Análise Completa do Sistema Narrativo - Fighting Fantasy RPG

**Data**: 2025-11-14
**Analista**: Claude (Sonnet 4.5)
**Objetivo**: Análise pente-fino do agente narrador, RAG, validações e ferramentas LLM

---

## 📊 RESUMO EXECUTIVO

### ✅ Pontos Fortes
- Sistema LangGraph bem estruturado (6 nodes)
- Prompt híbrido inteligente (liberdade criativa + restrições rígidas)
- Validação básica de ações implementada
- RAG integrado com Weaviate
- Histórico e flags mantidos

### ⚠️ Pontos Críticos Encontrados
1. **LLM NÃO tem acesso direto a tools** (não usa agent pattern)
2. **RAG limitado** (k=1, sem validação robusta)
3. **Validação de navegação fraca** (exits não verificados contra RAG)
4. **Sistema de flags manual** (não auto-extraído do conteúdo)
5. **Sem memória de contexto espacial** (não sabe de onde veio/para onde pode ir)

---

## 1. 🎮 ANÁLISE DO WORKFLOW LANGGRAPH

### Estrutura Atual

```
┌─────────────────┐
│ validate_action │
└────────┬────────┘
         │
┌────────▼────────┐
│retrieve_context │
└────────┬────────┘
         │
┌────────▼──────────┐
│generate_narrative │
└────────┬──────────┘
         │
┌────────▼──────┐
│ update_state  │
└────────┬──────┘
         │
┌────────▼─────────┐
│check_game_over   │
└──────────────────┘
```

### ✅ O que está BOM

1. **Fluxo Linear Claro**: Validação → RAG → Geração → Atualização → Game Over
2. **Router Condicional**: Permite pular etapas em caso de erro
3. **Estado Centralizado**: `GameState` TypedDict bem definido
4. **Logging Robusto**: Logs em todos os pontos críticos
5. **Error Handling**: Try-catch em todos os nodes

### ⚠️ PROBLEMAS

#### 1.1 LLM NÃO Usa Tools como Agent

**Problema**: A LLM é apenas um gerador de texto. As funções como `update_character_stats`, `add_item`, `combat_round` são chamadas MANUALMENTE nos nodes Python, não pela LLM.

**Código Atual** (`nodes.py`):
```python
def _generate_general_narrative(state: GameState) -> Dict[str, Any]:
    llm = get_llm(temperature=0.8)
    chain = NARRATIVE_PROMPT | llm  # ❌ Apenas prompt → LLM, sem tools
    response = chain.invoke({...})
    return {"narrative_response": response.content}
```

**Impacto**:
- LLM não pode atualizar stats sozinha
- LLM não pode adicionar/remover itens
- LLM não pode validar navegação
- Toda lógica de atualização é hardcoded nos nodes

**Solução**:
```python
from langchain.agents import create_react_agent

def _generate_general_narrative(state: GameState) -> Dict[str, Any]:
    llm = get_llm(temperature=0.7)

    tools = [
        update_character_stats,
        add_item,
        remove_item,
        check_item,
        try_move_to,
        roll_dice,
        check_luck,
    ]

    agent = create_react_agent(llm, tools, NARRATIVE_PROMPT)
    result = agent.invoke(state)

    return {
        **state,
        "narrative_response": result["output"],
        "tool_calls": result.get("tool_calls", [])
    }
```

---

## 2. 🗺️ ANÁLISE DO RAG (Retrieval Augmented Generation)

### Implementação Atual

**Código** (`nodes.py:97-136`):
```python
def retrieve_context_node(state: GameState) -> Dict[str, Any]:
    if action_type == "navigation":
        section_data = get_section_by_number(book_class_name, current_section)
    else:
        query = f"seção {current_section} {state['player_action']}"
        results = search_section(book_class_name, query, k=1)  # ❌ k=1
        section_data = results[0] if results else None
```

### ⚠️ PROBLEMAS

#### 2.1 RAG Muito Limitado (k=1)

**Problema**: Busca apenas 1 resultado. Se o embedding não for perfeito, perde contexto importante.

**Solução**:
```python
# Buscar top-3 e consolidar
results = search_section(book_class_name, query, k=3)

# Priorizar seção atual, mas incluir contexto
section_data = None
context_sections = []

for result in results:
    if result.get("section") == current_section:
        section_data = result  # Seção atual tem prioridade
    else:
        context_sections.append(result)  # Contexto adicional

# Passar ambos para LLM
return {
    **state,
    "section_content": section_data.get("content", ""),
    "context_sections": context_sections,  # Novo campo
    "section_metadata": section_data.get("metadata", {}),
}
```

#### 2.2 Sem Validação de Relevância

**Problema**: Não verifica se o resultado do RAG é realmente da seção correta.

**Solução**:
```python
def validate_rag_result(result: dict, expected_section: int) -> bool:
    """Valida se resultado RAG é da seção esperada."""
    returned_section = result.get("metadata", {}).get("section")

    if returned_section != expected_section:
        logger.warning(
            f"RAG retornou seção {returned_section}, "
            f"esperado {expected_section}"
        )
        return False

    # Verificar similaridade mínima
    score = result.get("score", 0)
    if score < 0.7:  # Threshold
        logger.warning(f"Score RAG baixo: {score}")
        return False

    return True
```

---

## 3. 🛡️ ANÁLISE DE VALIDAÇÃO E ANTI-ALUCINAÇÃO

### Sistema Atual: `RigidStructureValidator`

**Código** (`narrative_agent.py:83-137`):
```python
class RigidStructureValidator:
    def validate_navigation(self, current, target, visited, flags):
        # ✅ Impede voltar >10 seções
        if target_section < current_section - 10:
            return {"valid": False, ...}

    def validate_item_pickup(self, item_name, section, inventory):
        # ✅ Limita inventário a 12 itens
        if len(inventory) >= 12:
            return {"valid": False, ...}

    def validate_action(self, action, section, flags, in_combat):
        # ✅ Força resolver combate
        # ✅ Valida chave para porta
```

### ✅ O que está BOM

1. Validação de combate (deve atacar/fugir)
2. Limite de inventário
3. Validação básica de flags (chave para porta)
4. Impede backtracking excessivo

### ⚠️ PROBLEMAS CRÍTICOS

#### 3.1 Não Valida Exits Contra RAG

**Problema**: Não verifica se a seção de destino está realmente conectada.

**Código Atual** (`navigation.py:91-120`):
```python
def try_move_to(target_section, current_section, current_exits, ...):
    if target_section not in current_exits:  # ✅ Valida contra exits fornecidos
        return {"success": False, ...}
```

**MAS**: `current_exits` vem de onde? Se LLM pode inventar, problema não resolvido!

**Solução**:
```python
def validate_exits_from_rag(current_section: int, book_class: str) -> List[int]:
    """Extrai exits REAIS do RAG para a seção atual."""
    section_data = get_section_by_number(book_class, current_section)

    # Extrair números de seções do texto
    import re
    content = section_data.get("content", "")

    # Padrões comuns em Fighting Fantasy
    patterns = [
        r"vá para (?:a seção )?(\d+)",
        r"seção (\d+)",
        r"para o parágrafo (\d+)",
        r"volte para (\d+)",
    ]

    exits = set()
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        exits.update([int(m) for m in matches])

    # Adicionar exits do metadata se existir
    metadata_exits = section_data.get("metadata", {}).get("exits", [])
    exits.update(metadata_exits)

    return sorted(list(exits))
```

#### 3.2 Sem Whitelist de Itens

**Problema**: Validação de itens é inexistente. LLM pode inventar "Espada Mágica do Dragão Dourado".

**Solução**:
```python
# Em cada livro, definir itens permitidos
BOOK_ITEM_WHITELISTS = {
    "WarriorOfBlood": {
        # Seção: [itens permitidos]
        1: ["LANTERNA", "ESPADA", "MOCHILA"],
        5: ["CHAVE_DE_OURO", "POÇÃO_VERMELHA"],
        12: ["MAPA_ANTIGO", "PEDRA_RÚNICA"],
        # ... etc
    }
}

def validate_item_pickup(item: str, section: int, book: str) -> bool:
    """Valida se item pode ser pego nesta seção."""
    allowed = BOOK_ITEM_WHITELISTS.get(book, {}).get(section, [])
    item_normalized = item.upper().replace(" ", "_")

    if item_normalized not in allowed:
        logger.warning(
            f"Item '{item}' não permitido na seção {section}. "
            f"Permitidos: {allowed}"
        )
        return False

    return True
```

#### 3.3 Sistema de Flags Manual

**Problema**: Flags são setados manualmente. Não são extraídos automaticamente do RAG.

**Solução**:
```python
def extract_flags_from_section(section_content: str) -> Dict[str, Any]:
    """Extrai flags automaticamente do conteúdo da seção."""
    flags = {}

    content_lower = section_content.lower()

    # Detectar combate
    if any(w in content_lower for w in ["lute", "combate", "ataque"]):
        flags["combat_required"] = True

    # Detectar testes
    if "teste sua sorte" in content_lower:
        flags["luck_test_required"] = True
    if "teste sua habilidade" in content_lower:
        flags["skill_test_required"] = True

    # Detectar itens obrigatórios
    if "você precisa" in content_lower or "necessário" in content_lower:
        # Tentar extrair item
        match = re.search(r"(?:precisa|necessário)\s+(?:de\s+)?(\w+)", content_lower)
        if match:
            flags["required_item"] = match.group(1).upper()

    # Detectar portas/bloqueios
    if "porta trancada" in content_lower or "bloqueado" in content_lower:
        flags["door_locked"] = True

    return flags
```

---

## 4. 📖 ANÁLISE: HISTÓRIA FIEL AO LIVRO

### Prompt Híbrido (Genial!)

**Arquivo**: `narrative_agent.py:6-80`

```python
HYBRID_NARRATIVE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
    ### ✅ LIBERDADE CRIATIVA (Você PODE):
    1. Diálogos Ricos com NPCs
    2. Descrições Sensoriais
    3. Combate Tático
    4. Exploração Livre

    ### ❌ RESTRIÇÕES RÍGIDAS (Você NÃO PODE):
    1. Inventar itens não whitelisted
    2. Permitir navegação não conectada
    3. Pular etapas obrigatórias
    4. Alterar mecânica de dados
    5. Trair personalidade de NPCs
    """)
])
```

### ✅ EXCELENTE

1. **Filosofia Híbrida**: Permite criatividade MAS com guardrails
2. **Instruções Claras**: ✅ pode vs ❌ não pode
3. **Exemplos Concretos**: Mostra o que é boa narrativa
4. **Menção ao RAG**: "Use section_content como BASE"
5. **Esconde Números**: Não menciona "vá para seção 285"

### ⚠️ PROBLEMA

**Prompt sozinho não garante compliance**. LLM pode ignorar se não houver validação técnica.

**Solução**: Validação pós-geração

```python
def validate_narrative_compliance(narrative: str, allowed_items: List[str]) -> Dict:
    """Valida se narrativa inventou itens/seções proibidos."""
    issues = []

    # Verificar itens inventados
    # Extrair todos os substantivos próprios em MAIÚSCULAS
    potential_items = re.findall(r'\b[A-Z][A-Z_]+\b', narrative)

    for item in potential_items:
        if item not in allowed_items and item not in COMMON_WORDS:
            issues.append({
                "type": "invented_item",
                "item": item,
                "severity": "high"
            })

    # Verificar menção de números de seção
    if re.search(r'(?:seção|parágrafo|página)\s+\d+', narrative, re.IGNORECASE):
        issues.append({
            "type": "section_number_leak",
            "severity": "medium"
        })

    return {
        "compliant": len(issues) == 0,
        "issues": issues
    }
```

---

## 5. 🎭 ANÁLISE: LIBERDADE DE AÇÕES DO JOGADOR

### ✅ MUITO BOM!

O prompt permite:
- **Exploração livre**: "examinar", "cheirar", "procurar"
- **Conversas naturais**: NPCs não são menus
- **Táticas criativas**: Investidas, esquivas, etc
- **Ações atmosféricas**: "Você fareja o ar..."

**Exemplo do Prompt**:
```
4. **Exploração Livre:**
   - Jogador pode procurar, examinar, cheirar
   - Responda com flavor text rico
   - Se não há nada, diga de forma interessante
```

### ⚠️ PROBLEMA

Sem **sistema de consequências** para ações criativas.

**Exemplo**:
- Jogador: "Eu jogo areia nos olhos do orc"
- Sistema deveria: Testar HABILIDADE e dar bônus temporário

**Solução**: Adicionar campo `action_effects` no state

```python
def detect_creative_action_effects(action: str, enemy_type: str) -> Dict:
    """Detecta ações criativas e retorna efeitos."""
    action_lower = action.lower()

    effects = {
        "combat_modifier": 0,
        "narrative_bonus": "",
        "requires_test": None
    }

    # Jogar areia/cegar
    if any(w in action_lower for w in ["areia", "cegar", "olhos"]):
        effects["combat_modifier"] = +2  # Bônus próximo ataque
        effects["narrative_bonus"] = "O inimigo está momentaneamente cego!"
        effects["requires_test"] = "skill"  # Precisa passar em teste

    # Desarmar
    if "desarmar" in action_lower:
        effects["combat_modifier"] = +3
        effects["narrative_bonus"] = "Você desarma o inimigo!"
        effects["requires_test"] = "skill"
        effects["difficulty"] = +2  # Mais difícil

    return effects
```

---

## 6. 🚩 ANÁLISE: SISTEMA DE FLAGS

### Implementação Atual

**State** (`state.py:29`):
```python
class GameState(TypedDict):
    flags: Dict[str, Any]  # Flags genéricos
```

### ✅ Uso Correto

```python
# Em validação
if "abrir porta" in action and not flags.get("has_key", False):
    return {"valid": False, "error": "Porta trancada"}
```

### ⚠️ PROBLEMAS

1. **Flags setados manualmente**: Desenvolvedor precisa lembrar
2. **Não extraídos do RAG**: Informação está no livro mas não é usada
3. **Sem persistência visual**: Jogador não vê flags ativas

**Solução**: Sistema de flags auto-extraído + UI

```python
# Auto-extração
flags_from_rag = extract_flags_from_section(section_content)
state["flags"].update(flags_from_rag)

# Persistir em GameSession
session.flags = state["flags"]
session.save()

# UI: Mostrar flags ativos
{
    "door_locked": "🔒 Porta trancada",
    "has_key_gold": "🔑 Chave de Ouro",
    "orc_defeated": "⚔️ Orc derrotado",
    "in_combat": "⚔️ Em combate com Goblin"
}
```

---

## 7. 🔧 ANÁLISE: FERRAMENTAS PARA LLM

### Tools Disponíveis (mas não usados!)

```python
# apps/game/tools/character.py
@tool
def update_character_stats(character_id, updates):
    """Atualiza stats do personagem."""

@tool
def get_character_state(character_id):
    """Busca estado atual."""

# apps/game/tools/inventory.py
@tool
def add_item(item_name, inventory):
    """Adiciona item."""

@tool
def remove_item(item_name, inventory):
    """Remove item."""

@tool
def check_item(item_name, inventory):
    """Verifica se tem item."""

@tool
def use_item(item_name, item_type, character_stats):
    """Usa item (poção)."""

# apps/game/tools/combat.py
@tool
def combat_round(character_skill, character_stamina, ...):
    """Executa rodada de combate."""

@tool
def start_combat(enemy_name, enemy_skill, enemy_stamina):
    """Inicia combate."""

# apps/game/tools/dice.py
@tool
def roll_dice(count, faces):
    """Rola dados."""

@tool
def check_luck(character_luck, favor_player):
    """Testa sorte."""

@tool
def check_skill(character_skill, difficulty):
    """Testa habilidade."""

# apps/game/tools/navigation.py
@tool
def get_current_section(section_number, adventure_name):
    """Busca seção no Weaviate."""

@tool
def try_move_to(target_section, current_section, current_exits, ...):
    """Valida e move para nova seção."""
```

### ❌ PROBLEMA CRÍTICO

**Tools existem mas LLM não tem acesso!**

Código atual apenas gera texto:
```python
llm = get_llm()
chain = NARRATIVE_PROMPT | llm  # ❌ Sem tools
response = chain.invoke({...})
```

### ✅ SOLUÇÃO: LangChain Agent

```python
from langchain.agents import create_react_agent, AgentExecutor

def create_game_master_agent():
    """Cria agent com acesso a todas as tools."""
    llm = get_llm(temperature=0.7)

    tools = [
        # Character
        update_character_stats,
        get_character_state,
        # Inventory
        add_item,
        remove_item,
        check_item,
        use_item,
        # Combat
        combat_round,
        start_combat,
        # Dice
        roll_dice,
        check_luck,
        check_skill,
        # Navigation
        get_current_section,
        try_move_to,
    ]

    # Criar agent ReAct (Reasoning + Acting)
    agent = create_react_agent(llm, tools, NARRATIVE_PROMPT)

    # Executor com limite de iterações
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,  # Evitar loops
        verbose=True
    )

    return executor

# Usar no node
def generate_narrative_node(state: GameState):
    agent = create_game_master_agent()

    result = agent.invoke({
        "input": state["player_action"],
        "character_stats": {...},
        "section_content": state["section_content"],
        # ... resto do contexto
    })

    return {
        **state,
        "narrative_response": result["output"],
        "intermediate_steps": result["intermediate_steps"]
    }
```

---

## 8. 📍 ANÁLISE: CONTEXTO ESPACIAL (de onde veio / onde está / para onde vai)

### Implementação Atual

```python
class GameState(TypedDict):
    current_section: int  # ✅ Onde está
    visited_sections: List[int]  # ✅ Histórico de seções
    history: List[Dict]  # ✅ Histórico de ações
```

### ⚠️ FALTANDO

1. **De onde veio**: Última seção não é explícita
2. **Para onde pode ir**: Exits não são claramente fornecidos
3. **Contexto de vizinhança**: Seções adjacentes não são mencionadas

### ✅ SOLUÇÃO: Contexto Espacial Enriquecido

```python
def enrich_spatial_context(state: GameState) -> Dict:
    """Enriquece estado com contexto espacial."""
    current = state["current_section"]
    visited = state["visited_sections"]

    # De onde veio (última seção visitada)
    previous_section = visited[-2] if len(visited) >= 2 else None

    # Para onde pode ir (exits da seção atual)
    current_section_data = get_section_by_number(
        state["book_class_name"],
        current
    )
    exits = extract_exits(current_section_data.get("content", ""))

    # Buscar informações das seções adjacentes (peek)
    exit_previews = {}
    for exit_num in exits:
        exit_data = get_section_by_number(state["book_class_name"], exit_num)
        # Apenas primeiras 100 chars para não spoilar
        preview = exit_data.get("content", "")[:100] + "..."
        exit_previews[exit_num] = preview

    return {
        "previous_section": previous_section,
        "current_exits": exits,
        "exit_previews": exit_previews,
        "sections_visited_count": len(set(visited)),
        "backtrack_depth": current - min(visited) if visited else 0
    }
```

**Passar para LLM**:
```python
spatial_context = enrich_spatial_context(state)

prompt_vars = {
    ...existing...,
    "previous_section": spatial_context["previous_section"],
    "available_exits": spatial_context["current_exits"],
    "exit_hints": spatial_context["exit_previews"]
}
```

---

## 9. 📋 CHECKLIST DE CONFORMIDADE

| Item | Status | Notas |
|------|--------|-------|
| **RAG integrado** | ✅ | Weaviate + vector search |
| **RAG robusto (k>1)** | ❌ | k=1, deveria ser k=3 |
| **RAG validado** | ❌ | Não verifica se resultado é correto |
| **Linha narrativa mantida** | ⚠️ | Histórico existe mas contexto fraco |
| **De onde veio / para onde vai** | ❌ | Não explícito |
| **Anti-alucinação - Itens** | ❌ | Sem whitelist |
| **Anti-alucinação - Exits** | ⚠️ | Validação existe mas não rigorosa |
| **Anti-alucinação - Stats** | ✅ | Stats validados (min 0) |
| **História fiel ao livro** | ✅ | Prompt excelente |
| **Liberdade de ações** | ✅ | Prompt permite criatividade |
| **Flags auto-extraídos** | ❌ | Manual |
| **Tools para LLM** | ❌ | Existem mas LLM não acessa |
| **Agent pattern** | ❌ | Não implementado |
| **Validação pós-geração** | ❌ | Não existe |

---

## 10. 🚀 PLANO DE MELHORIAS PRIORITÁRIAS

### Prioridade ALTA (Implementar AGORA)

#### 1. Transformar em LangChain Agent
```python
# Permitir LLM usar tools diretamente
agent = create_react_agent(llm, tools, prompt)
```

#### 2. RAG Robusto
```python
# k=3 com consolidação
results = search_section(book, query, k=3)
section_data = consolidate_results(results, current_section)
```

#### 3. Whitelist de Itens
```python
BOOK_ITEMS = {
    "WarriorOfBlood": {
        1: ["LANTERNA", "ESPADA"],
        5: ["CHAVE_OURO"],
        # ...
    }
}
```

#### 4. Validação Rigorosa de Exits
```python
actual_exits = extract_exits_from_rag(current_section)
if target not in actual_exits:
    return {"error": "Caminho não existe"}
```

### Prioridade MÉDIA (Próxima Sprint)

#### 5. Contexto Espacial
```python
spatial = enrich_spatial_context(state)
# previous_section, current_exits, exit_previews
```

#### 6. Flags Auto-Extraídos
```python
flags = extract_flags_from_section(content)
state["flags"].update(flags)
```

#### 7. Validação Pós-Geração
```python
compliance = validate_narrative_compliance(narrative, allowed_items)
if not compliance["compliant"]:
    # Regenerar com constraints mais fortes
```

### Prioridade BAIXA (Backlog)

#### 8. Sistema de Consequências
```python
effects = detect_creative_action_effects(action, enemy)
apply_combat_modifier(effects["combat_modifier"])
```

#### 9. UI de Flags Ativos
```html
<div class="flags-panel">
    🔒 Porta trancada
    🔑 Chave de Ouro
</div>
```

#### 10. Telemetria de Alucinações
```python
# Log quando LLM tentar inventar algo
logger.warning(f"LLM tentou inventar item: {item}")
# Coletar métricas
```

---

## 11. 🎯 CONCLUSÃO

### Sistema Atual: 7/10

**Pontos Fortes**:
- Arquitetura sólida (LangGraph)
- Prompt híbrido inteligente
- RAG integrado
- Validação básica funcionando

**Pontos Fracos**:
- LLM não é agent (tools não acessíveis)
- RAG limitado (k=1)
- Validação de itens/exits fraca
- Sem whitelist
- Flags manuais

### Após Melhorias: 9.5/10

Com as mudanças prioritárias:
- ✅ Agent pattern com tools
- ✅ RAG robusto (k=3)
- ✅ Whitelist de itens
- ✅ Exits validados contra RAG
- ✅ Flags auto-extraídos
- ✅ Contexto espacial rico

**Resultado**: Sistema **production-ready** e **fiel aos livros Fighting Fantasy** com liberdade criativa controlada!

---

## 12. 📝 PRÓXIMOS PASSOS

1. **Revisar este documento** com time
2. **Priorizar melhorias** (alta/média/baixa)
3. **Criar issues** no GitHub para cada melhoria
4. **Implementar** em sprints
5. **Testar** com jogadores reais
6. **Iterar** baseado em feedback

**Documentado por**: Claude Sonnet 4.5
**Data**: 2025-11-14
**Versão**: 1.0
