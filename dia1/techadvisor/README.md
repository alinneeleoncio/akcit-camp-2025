## TechAdvisor – Seu primeiro agente com LangChain + LangGraph

Um agente simples que recomenda tecnologias para estudar com base no seu interesse. Ele demonstra, de forma didática, como:
- **carregar variáveis de ambiente** com `python-dotenv`;
- **construir prompts** com `PromptTemplate` (LangChain);
- **orquestrar um fluxo** com `LangGraph` utilizando um `StateGraph` com nós e arestas;
- **conectar um LLM da OpenAI** via `langchain-openai` usando a interface moderna (LCEL): `prompt | llm | StrOutputParser()`.

### Por que este projeto?
- Ideal para bootcamps e primeiros passos em agentes de IA.
- Código curto, claro e comentado para facilitar o aprendizado.

---

## Pré‑requisitos
- Python 3.12+ (recomendado)
- Conta e chave de API da OpenAI
- macOS, Linux ou Windows com terminal

---

## Setup rápido (macOS/Linux)

1) Clonar o repositório (ou abrir a pasta no seu ambiente):
```bash
cd /Users/seu-usuario/algum/lugar
git clone <seu-repo>.git
cd akcit/akcit-camp-2025/dia1
```

2) Criar e ativar o ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Instalar as dependências específicas do agente:
```bash
pip install -r techadvisor/requirements.txt
```

4) Configurar as variáveis de ambiente:
```bash
cp .env-sample .env
# edite o arquivo .env e coloque sua chave real
# OPENAI_API_KEY=sk-....
```

> Dica: O arquivo `.env-sample` já existe na raiz do projeto. É só copiar para `.env` e preencher a chave.

### Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r techadvisor\requirements.txt
copy .env-sample .env
# edite .env e informe OPENAI_API_KEY
```

---

## Como rodar
Com o ambiente virtual ativo e `.env` configurado:
```bash
python techadvisor/techadvisor_agent.py
```

Exemplo de uso (interativo):
```
🤖 TechAdvisor - Recomenda tecnologias com base em seus interesses!

O que você quer aprender ou melhorar? (ou 'sair'): back-end com Python

🔎 Resposta do agente:
Sugestão: Estude FastAPI...
------------------------------------------------------------
```

Para sair, digite `sair` (ou `exit`/`quit`).

---

## Como funciona (arquitetura didática)

- `PromptTemplate` (LangChain): define o texto-base com variável `{interesse}`.
- `ChatOpenAI` (langchain-openai): cria o LLM (modelo da OpenAI) a ser usado.
- `LCEL` (LangChain Expression Language): conectamos `prompt | llm | StrOutputParser()` formando uma pipeline:
  - `prompt` injeta o `{interesse}`
  - `llm` gera a resposta
  - `StrOutputParser()` garante que o resultado final seja string limpa
- `LangGraph`:
  - Criamos um `StateGraph(dict)`, onde o estado é um dicionário com chaves como `interesse` e `resposta`.
  - Adicionamos um nó `recomendador` que lê `interesse`, chama a pipeline e grava `resposta` no estado.
  - Definimos o ponto de entrada e uma aresta para `END` (fluxo simples de 1 passo).

Fluxo resumido:
1) Usuário digita um interesse.
2) O estado entra no nó `recomendador`.
3) A pipeline `prompt | llm | parser` roda e retorna um texto.
4) O texto é salvo em `state['resposta']` e exibido.

### Diagrama do grafo (Mermaid)

```mermaid
flowchart LR
    entry([Entry Point]) --> R["Nó: recomendador<br/>(prompt | llm | StrOutputParser)"]
    R --> end([END_NODE])

    %% Anotações de estado (conceituais)
    subgraph Estado ["Estado"]
      I["state['interesse']"] 
      O["state['resposta']"]
    end
    
    I -->|input do usuário| R
    R --> O
```

---

## Estrutura dos arquivos
- `techadvisor/techadvisor_agent.py`: código do agente (altamente comentado).
- `techadvisor/requirements.txt`: dependências específicas.
- `.env-sample`: modelo de variáveis de ambiente (na raiz do projeto).

---

## Personalizações comuns

- **Trocar o modelo**: no arquivo `techadvisor_agent.py`, altere `model="gpt-4o-mini"` para outro modelo compatível na sua conta.
- **Ajustar criatividade**: modifique `temperature=0.7`.
- **Mudar o prompt**: edite o `template_text` para orientar o agente a outro domínio (por exemplo, carreiras, cloud, dados, etc.).
- **Adicionar etapas**: crie novos nós no `StateGraph` (por exemplo, um nó que valida a entrada do usuário antes de chamar o LLM) e conecte-os com `add_edge`.

---

## Problemas comuns e soluções

- "ModuleNotFoundError: No module named 'langchain_openai'"
  - Rode: `pip install -r techadvisor/requirements.txt` com o venv ativo.

- "API key inválida ou ausente"
  - Verifique seu `.env` e se o terminal tem `OPENAI_API_KEY` carregada. Você pode testar com `python -c "import os; print(os.getenv('OPENAI_API_KEY'))"`.

- "DeprecationWarning sobre LLMChain"
  - Já migramos para `prompt | llm | StrOutputParser()`; se notar algo semelhante, confira se está rodando a versão mais recente do arquivo.

- Conflitos de versões
  - Atualize dependências: `pip install -U -r techadvisor/requirements.txt`.
  - Em casos extremos, recrie o venv.

---

## Próximos passos sugeridos no bootcamp

- Criar um segundo nó que peça esclarecimentos quando o interesse for muito genérico.
- Persistir conversas ou métricas com `langsmith`.
- Conectar fontes externas (documentos, web) e usar RAG.
- Adicionar ferramenta de busca e um roteador de nós no `LangGraph`.

---

## Licença
Projeto educacional para uso em bootcamp. Adapte livremente conforme necessário.


