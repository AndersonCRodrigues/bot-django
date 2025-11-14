# Game Master Prompts

Este diretório contém os prompts do sistema de Narrador Mestre (Game Master) para o RPG Fighting Fantasy.

## Estrutura

```
prompts/
├── __init__.py
├── game_master.py  # Prompt principal do GM
└── README.md       # Este arquivo
```

## Uso

### Importação

```python
from apps.game.prompts import get_game_master_prompt

# Gerar o prompt para uma sessão específica
prompt = get_game_master_prompt(
    character_id="507f1f77bcf86cd799439011",
    adventure_name="FeiticeiroDaMontanhaFogo"
)
```

### Integração com LangChain

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from apps.game.tools import (
    get_character_state,
    update_character_stats,
    add_item,
    remove_item,
    check_item,
    use_item,
    roll_dice,
    check_luck,
    check_skill,
    start_combat,
    combat_round,
    get_current_section,
    try_move_to,
)
from apps.game.prompts import get_game_master_prompt

# 1. Configurar o LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.7,
    google_api_key=settings.GOOGLE_API_KEY,
)

# 2. Preparar as ferramentas
tools = [
    get_character_state,
    update_character_stats,
    add_item,
    remove_item,
    check_item,
    use_item,
    roll_dice,
    check_luck,
    check_skill,
    start_combat,
    combat_round,
    get_current_section,
    try_move_to,
]

# 3. Gerar o prompt do GM
system_prompt = get_game_master_prompt(
    character_id=character_id,
    adventure_name=adventure_name
)

# 4. Criar o prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 5. Criar o agente
agent = create_tool_calling_agent(llm, tools, prompt_template)

# 6. Criar o executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10,
)

# 7. Executar
response = agent_executor.invoke({
    "input": "Vou seguir o corredor à esquerda",
    "chat_history": []
})

print(response["output"])
```

## Características do Prompt

### 1. **Baseado em Ferramentas**
O prompt foi adaptado para trabalhar com as ferramentas LangChain existentes no sistema:

- **Character**: `get_character_state()`, `update_character_stats()`
- **Inventory**: `add_item()`, `remove_item()`, `check_item()`, `use_item()`
- **Dice**: `roll_dice()`, `check_luck()`, `check_skill()`
- **Combat**: `start_combat()`, `combat_round()`
- **Navigation**: `get_current_section()`, `try_move_to()`

### 2. **Sistema de Combate Manual**
O prompt **NÃO recomenda usar `combat_round()`** automático, pois ele rola dados pelo jogador automaticamente, o que conflita com a filosofia Fighting Fantasy onde o jogador deve rolar seus próprios dados.

Em vez disso, o prompt fornece um **sistema de combate manual** onde:
- O GM rola dados para NPCs usando `roll_dice("2d6")`
- O GM solicita ao jogador rolar seus dados com `[ROLE 2d6]`
- Permite Testes de Sorte entre a determinação do acerto e a aplicação do dano

### 3. **Testes de Sorte Manuais**
Similar ao combate, o prompt recomenda **não usar `check_luck()`** diretamente, pois ela rola dados automaticamente.

O fluxo manual permite:
- Solicitar `[ROLE 2d6]` ao jogador
- Comparar com a Sorte atual
- Reduzir a Sorte manualmente via `update_character_stats()`

### 4. **Validação de Estado**
O prompt enfatiza que o agente **NUNCA deve confiar na memória conversacional** para dados de estado.

**Sempre:**
1. Chamar `get_character_state()` antes de decisões
2. Chamar `update_character_stats()` imediatamente após determinar uma mudança
3. Narrar mudanças DEPOIS de atualizar via ferramenta

### 5. **Narrativa Imersiva**
O prompt proíbe:
- Menção a números de seção
- Comandos técnicos ("vá para X")
- Linguagem fora do universo
- Referências a "sistema", "ferramentas", "código"

### 6. **IDs Contextualizados**
O prompt é gerado com os IDs específicos da sessão:
```python
character_id = "507f1f77bcf86cd799439011"
adventure_name = "FeiticeiroDaMontanhaFogo"
```

Todas as chamadas de ferramentas no prompt usam esses valores.

## Modificações Futuras

### Adicionar Novas Ferramentas

Se você criar novas ferramentas em `/apps/game/tools/`, atualize o prompt para incluir:

1. **Documentação da ferramenta** (seção 3)
2. **Quando usar** (seção 4)
3. **Exemplos de uso** (seção 8)

### Ajustar o Tom Narrativo

Modifique a seção 1 (Persona e Objetivo) para alterar o tom:
- Mais amigável vs. implacável
- Mais descritivo vs. conciso
- Mais orientado a ação vs. exploração

### Configurar Dificuldade

Ajuste as regras nas seções 4.2-4.4 para:
- Modificadores de testes
- Dano de combate
- Recuperação de atributos

## Troubleshooting

### O agente não está usando as ferramentas

**Problema:** O agente narra mudanças sem chamar ferramentas.

**Solução:**
- Certifique-se de que as ferramentas estão sendo passadas corretamente ao `create_tool_calling_agent()`
- Verifique se o modelo suporta tool calling (Gemini 2.0 Flash suporta)
- Aumente o `max_iterations` no `AgentExecutor`

### O agente está rolando dados automaticamente

**Problema:** O agente usa `check_luck()` ou `combat_round()` em vez do modo manual.

**Solução:**
- O prompt já recomenda o modo manual, mas o agente pode ignorar
- Considere **remover** `check_luck`, `check_skill` e `combat_round` da lista de ferramentas se quiser forçar o modo manual
- Ou deixe ambas as opções e monitore o comportamento

### Inconsistência de estado

**Problema:** O personagem tem itens que não foram adicionados via ferramenta.

**Solução:**
- Revise os logs do agente (`verbose=True`)
- Verifique se `update_character_stats()` e `add_item()`/`remove_item()` estão sendo chamadas
- Adicione validação extra no código que persiste o estado no MongoDB

## Referências

- **Ferramentas**: `/apps/game/tools/`
- **Modelos**: `/apps/game/models.py`
- **Validators**: `/apps/game/validators/`
- **LangChain Docs**: https://python.langchain.com/docs/
