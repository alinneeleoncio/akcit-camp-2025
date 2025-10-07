import os
from dotenv import load_dotenv
import gradio as gr

# Reutiliza o app (grafo compilado) já existente no módulo principal
# Suporta execução tanto via "python techadvisor/agente_gui.py" (import local)
# quanto via "python -m techadvisor.agente_gui" (import por pacote)
try:
    from techadvisor_agent import app
except ImportError:
    from techadvisor.techadvisor_agent import app


load_dotenv()


def init_chat():
    state = {}
    result = app.invoke(state)
    state.update(result)
    history = []
    history.append([None, state.get("resposta", "Olá! Eu sou o TechAdvisor. Como posso te chamar?")])
    return history, state


def chat_turn(user_message: str, history: list, state: dict):
    state = state or {}
    text = (user_message or "").strip()

    if text.lower() in ["/reset", "sair", "exit", "quit"]:
        # Reinicia a conversa e envia nova saudação
        state = {}
        result = app.invoke(state)
        state.update(result)
        history = []
        history.append([None, state.get("resposta", "Olá! Eu sou o TechAdvisor. Como posso te chamar?")])
        return history, state

    state["mensagem_usuario"] = text
    result = app.invoke(state)
    state.update(result)

    reply = state.get("resposta", "Desculpe, não consegui responder agora.")
    history = history + [[user_message, reply]]
    return history, state


with gr.Blocks(title="TechAdvisor - Chat") as demo:
    gr.Markdown("## 🤖 TechAdvisor – Chat sobre tecnologia")
    chatbot = gr.Chatbot(height=420)
    state = gr.State({})
    msg = gr.Textbox(label="Mensagem", placeholder="Diga 'tchau' para encerrar ou '/reset' para recomeçar")
    send = gr.Button("Enviar")

    demo.load(fn=init_chat, outputs=[chatbot, state])
    send.click(fn=chat_turn, inputs=[msg, chatbot, state], outputs=[chatbot, state])
    msg.submit(fn=chat_turn, inputs=[msg, chatbot, state], outputs=[chatbot, state])

    def _clear_input():
        return ""

    send.click(fn=_clear_input, outputs=msg)
    msg.submit(fn=_clear_input, outputs=msg)


if __name__ == "__main__":
    # servidor local padrão; para compartilhar publicamente, use share=True
    demo.launch()


