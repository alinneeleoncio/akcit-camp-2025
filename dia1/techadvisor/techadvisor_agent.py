# ============================================================
# TechAdvisor – Agente conversacional com LangChain + LangGraph
# ============================================================
# Objetivo didático:
# - Mostrar como conectar um LLM (OpenAI) usando a integração moderna `langchain-openai`.
# - Ensinar a criar um `PromptTemplate` e compor uma pipeline com LCEL: `prompt | llm | parser`.
# - Demonstrar a orquestração de um fluxo com múltiplos nós no LangGraph (`StateGraph`).
# - Rodar de forma interativa no terminal, guiando o usuário por boas‑vindas, coleta de nome e Q&A.

import os
import re
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
# 3. Definir o PromptTemplate (para Q&A após conhecer o nome)
# ============================================================
# O PromptTemplate permite parametrizar trechos do prompt, como `{interesse}`.
# No momento de executar, substituiremos esse placeholder pelo valor fornecido
# pelo usuário no estado do LangGraph.
template_text = (
    "Você é o TechAdvisor, um especialista amigável em tecnologia e programação.\n"
    "Converse de forma objetiva, em português, com o usuário {nome}.\n"
    "Pergunta do usuário: {pergunta}\n\n"
    "Responda de forma curta e útil. Quando adequado, recomende tecnologias, frameworks, "
    "boas práticas ou próximos passos de estudo."
)
prompt = PromptTemplate(
    input_variables=["nome", "pergunta"],
    template=template_text
)

# ============================================================
# 4. Criar uma pipeline LCEL (Prompt -> Modelo -> Parser) para Q&A
# ============================================================
# LCEL (LangChain Expression Language) permite compor etapas como um pipeline.
# Aqui encadeamos:
#   1) prompt: recebe `{interesse}` e gera a string final de instrução
#   2) llm: chama o modelo de chat da OpenAI com esse prompt
#   3) StrOutputParser(): converte a resposta para uma string simples
qa_chain = prompt | llm | StrOutputParser()

# ============================================================
# 5. Integrar a pipeline dentro de um fluxo com LangGraph (múltiplos nós)
# ============================================================
# O estado é um dicionário com chaves como:
# - etapa: controla o próximo nó ("boas_vindas" | "aguardar_nome" | "responder_perguntas" | "fim")
# - mensagem_usuario: última entrada do usuário
# - nome: nome do usuário, quando capturado
# - resposta: última resposta do agente (saída para UI/CLI)
# - historico: lista opcional de trocas (para futura expansão)

def extrair_nome(texto: str) -> str:
    """Heurística simples: usa a frase inteira como nome, limpando espaços e pontuação leve."""
    if not texto:
        return ""
    candidato = texto.strip()
    # Remove aspas e pontuação nas pontas
    candidato = re.sub(r'^["\'\s]+|["\'\s]+$', "", candidato)
    # Capitaliza primeiro nome/partes
    partes = [p.capitalize() for p in re.split(r"\s+", candidato) if p]
    return " ".join(partes)


def boas_vindas_node(state: dict) -> dict:
    state["resposta"] = "Olá! Eu sou o TechAdvisor. Como posso te chamar?"
    state["etapa"] = "aguardar_nome"
    return state


def aguardar_nome_node(state: dict) -> dict:
    mensagem = (state.get("mensagem_usuario") or "").strip()
    if not mensagem:
        state["resposta"] = "Não entendi. Qual é o seu nome?"
        state["etapa"] = "aguardar_nome"
        return state

    nome = extrair_nome(mensagem)
    if not nome:
        state["resposta"] = "Poderia repetir seu nome, por favor?"
        state["etapa"] = "aguardar_nome"
        return state

    state["nome"] = nome
    state.setdefault("historico", [])
    state["resposta"] = f"Prazer, {nome}! Como posso ajudar em tecnologia hoje?"
    state["etapa"] = "responder_perguntas"
    return state


def responder_perguntas_node(state: dict) -> dict:
    mensagem = (state.get("mensagem_usuario") or "").strip()
    nome = state.get("nome", "usuário")

    if mensagem.lower() == "tchau" or "tchau" in mensagem.lower():
        state["resposta"] = f"Até logo, {nome}! 👋"
        state["etapa"] = "fim"
        state["encerrar"] = True
        return state

    # Gera resposta via LLM
    resposta = qa_chain.invoke({
        "nome": nome,
        "pergunta": mensagem or "Me diga algo legal sobre tecnologia."
    })

    # Atualiza histórico simples
    historico = state.setdefault("historico", [])
    if mensagem:
        historico.append({"role": "user", "content": mensagem})
    historico.append({"role": "assistant", "content": resposta})

    state["resposta"] = resposta
    state["etapa"] = "responder_perguntas"
    state["encerrar"] = False
    return state


def roteador_node(state: dict) -> dict:
    # Nó "inócuo" apenas para permitir arestas condicionais
    return state


def proxima_parada(state: dict) -> str:
    # Verifica a etapa atual do estado
    etapa = state.get("etapa")
    if etapa == "aguardar_nome":
        return "aguardar_nome"
    if etapa == "responder_perguntas":
        return "responder_perguntas"
    if etapa == "fim":
        return "fim"
    # Padrão: início do fluxo
    return "boas_vindas"


# Criar o grafo do agente com múltiplos nós
graph = StateGraph(dict)

graph.add_node("roteador", roteador_node)
graph.add_node("boas_vindas", boas_vindas_node)
graph.add_node("aguardar_nome", aguardar_nome_node)
graph.add_node("responder_perguntas", responder_perguntas_node)

# Configura o roteamento dinâmico entre os nós do grafo
# - O nó "roteador" consulta a função proxima_parada() para decidir o próximo destino
# - A função proxima_parada() verifica state["etapa"] e retorna uma das strings:
#   - "boas_vindas": inicia o fluxo com saudação
#   - "aguardar_nome": espera input do nome do usuário 
#   - "responder_perguntas": processa perguntas via LLM
#   - "fim": encerra o fluxo (END)
# - As arestas condicionais mapeiam cada retorno ao nó correspondente
graph.add_conditional_edges(
    "roteador",
    proxima_parada,
    {
        "boas_vindas": "boas_vindas",
        "aguardar_nome": "aguardar_nome",
        "responder_perguntas": "responder_perguntas",
        "fim": END,
    },
)

# Cada nó executa uma "única rodada" e retorna para o chamador
graph.add_edge("boas_vindas", END)
graph.add_edge("aguardar_nome", END)
graph.add_edge("responder_perguntas", END)

graph.set_entry_point("roteador")

# Compila o grafo em um executor (cria um app pronto para .invoke)
app = graph.compile()

# ============================================================
# 6. Execução interativa (simulação de uso)
# ============================================================
# Loop de CLI simples para interagir com o agente.
# A cada entrada do usuário, invocamos o grafo passando um estado inicial
# com a chave "interesse" e depois exibimos a chave "resposta".
if __name__ == "__main__":
    print("🤖 TechAdvisor - Agente conversacional sobre tecnologia\n")

    # Estado de conversa persistente entre rodadas
    state: dict = {}

    # Primeira saudação
    result = app.invoke(state)
    state.update(result)
    print(state.get("resposta", "Olá!"))

    while True:
        try:
            mensagem = input("\nVocê: ")
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando o agente. Até logo!")
            break

        if mensagem.lower() in ["sair", "exit", "quit"]:
            print("Encerrando o agente. Até logo!")
            break

        # Preenche a última mensagem e invoca 1 passo do grafo
        state["mensagem_usuario"] = mensagem
        result = app.invoke(state)
        state.update(result)

        print(f"\n🔎 Agente: {state.get('resposta', '')}")

        if state.get("etapa") == "fim" or state.get("encerrar"):
            print("\nConversa encerrada.")
            break
