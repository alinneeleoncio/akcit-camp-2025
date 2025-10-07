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


def recomendar(interesse: str) -> str:
    if not interesse or not interesse.strip():
        return "Por favor, descreva seu interesse."
    result = app.invoke({"interesse": interesse.strip()})
    return result.get("resposta", "Não foi possível gerar uma recomendação.")


with gr.Blocks(title="TechAdvisor - Gradio") as demo:
    gr.Markdown("## 🤖 TechAdvisor – Recomenda tecnologias com IA")
    interesse = gr.Textbox(label="O que você quer aprender ou melhorar?", placeholder="Ex.: back-end com Python")
    btn = gr.Button("Recomendar")
    saida = gr.Textbox(label="Recomendação", lines=8)

    btn.click(fn=recomendar, inputs=interesse, outputs=saida)


if __name__ == "__main__":
    # servidor local padrão; para compartilhar publicamente, use share=True
    demo.launch()


