# ============================================================
# TechAdvisor – Seu primeiro agente com LangChain + LangGraph
# ============================================================
# Objetivo didático:
# - Mostrar como conectar um LLM (OpenAI) usando a integração moderna `langchain-openai`.
# - Ensinar a criar um `PromptTemplate` e compor uma pipeline com LCEL: `prompt | llm | parser`.
# - Demonstrar a orquestração de um fluxo simples com LangGraph (`StateGraph`).
# - Rodar de forma interativa no terminal, recebendo um interesse e retornando uma recomendação.

import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

# ============================================================
# 1. Carregar variáveis de ambiente
# ============================================================
# Busca um arquivo `.env` na raiz do projeto e carrega as variáveis
# (por exemplo, OPENAI_API_KEY). Assim, não precisamos exportar
# manualmente no terminal a cada execução.
load_dotenv()

# ============================================================
# 2. Definir o LLM (OpenAI via langchain-openai)
# ============================================================
# `ChatOpenAI` é o wrapper do LangChain para modelos de chat da OpenAI.
# Parâmetros principais:
# - model: nome do modelo (ajuste para o que sua conta permite).
# - temperature: controla a criatividade (0 = mais determinístico; 1 = mais criativo).
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

# ============================================================
# 3. Definir o PromptTemplate
# ============================================================
# O PromptTemplate permite parametrizar trechos do prompt, como `{interesse}`.
# No momento de executar, substituiremos esse placeholder pelo valor fornecido
# pelo usuário no estado do LangGraph.
template_text = (
    "Você é um assistente que recomenda tecnologias de programação "
    "com base no interesse do usuário.\n"
    "Usuário: {interesse}\n"
    "Responda em português e recomende uma tecnologia apropriada "
    "para o usuário aprender em seguida, explicando brevemente o porquê."
)
prompt = PromptTemplate(
    input_variables=["interesse"],
    template=template_text
)

# ============================================================
# 4. Criar uma pipeline LCEL (Prompt -> Modelo -> Parser)
# ============================================================
# LCEL (LangChain Expression Language) permite compor etapas como um pipeline.
# Aqui encadeamos:
#   1) prompt: recebe `{interesse}` e gera a string final de instrução
#   2) llm: chama o modelo de chat da OpenAI com esse prompt
#   3) StrOutputParser(): converte a resposta para uma string simples
chain = prompt | llm | StrOutputParser()

# ============================================================
# 5. Integrar a pipeline dentro de um fluxo com LangGraph
# ============================================================
# Usamos um grafo de estado (StateGraph) onde cada nó recebe e devolve
# um dicionário. Assim fica fácil adicionar múltiplos passos no futuro.

# Definição do estado (cada nó lê e atualiza esse dicionário)
def techadvisor_node(state: dict):
    # Extraímos o interesse do usuário que foi inserido no estado
    interesse = state["interesse"]

    # Executamos a pipeline LCEL passando a variável do prompt
    resposta = chain.invoke({"interesse": interesse})

    # Gravamos a saída no estado para outros nós (ou a etapa final) consumirem
    state["resposta"] = resposta
    return state

# Criar o grafo do agente
graph = StateGraph(dict)

# Adiciona um nó "recomendador" que utiliza a pipeline definida acima
graph.add_node("recomendador", techadvisor_node)

# Define o ponto inicial e o final do fluxo
# Entrada -> recomendador -> END
graph.set_entry_point("recomendador")
graph.add_edge("recomendador", END)

# Compila o grafo em um executor (cria um app pronto para .invoke)
app = graph.compile()

# ============================================================
# 6. Execução interativa (simulação de uso)
# ============================================================
# Loop de CLI simples para interagir com o agente.
# A cada entrada do usuário, invocamos o grafo passando um estado inicial
# com a chave "interesse" e depois exibimos a chave "resposta".
if __name__ == "__main__":
    print("🤖 TechAdvisor - Recomenda tecnologias com base em seus interesses!\n")
    while True:
        interesse = input("O que você quer aprender ou melhorar? (ou 'sair'): ")
        if interesse.lower() in ["sair", "exit", "quit"]:
            print("Encerrando o agente. Até logo!")
            break
        # Executa o fluxo LangGraph com o estado inicial contendo o interesse
        result = app.invoke({"interesse": interesse})
        print("\n🔎 Resposta do agente:")
        print(result["resposta"])
        print("-" * 60)
