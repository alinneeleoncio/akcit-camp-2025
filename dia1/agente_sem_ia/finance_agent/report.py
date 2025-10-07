from __future__ import annotations
from typing import Dict
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

def _page_title(pdf, title: str):
    fig = plt.figure(figsize=(11, 8.5))
    plt.axis("off")
    plt.text(0.5, 0.6, title, ha="center", va="center", fontsize=22, fontweight="bold")
    plt.text(0.5, 0.48, f"Gerado: {datetime.now():%Y-%m-%d %H:%M}", ha="center", va="center", fontsize=10)
    pdf.savefig(fig)
    plt.close(fig)

def plot_per_ticker(pdf: PdfPages, dfs: Dict[str, pd.DataFrame]):
    for ticker, df in dfs.items():
        cols = [c for c in ["close","mm20","mm50"] if c in df.columns]
        if not cols:
            continue
        ax = df.plot(x="date", y=cols, title=f"Preço e MMs - {ticker}", figsize=(11, 4))
        ax.set_xlabel("Data")
        ax.set_ylabel("Preço")
        pdf.savefig(ax.figure); plt.close(ax.figure)

def plot_comparison(pdf: PdfPages, dfs: Dict[str, pd.DataFrame]):
    frames = []
    for t, d in dfs.items():
        if "ret_acum" in d.columns:
            frames.append(d[["date","ret_acum"]].set_index("date").rename(columns={"ret_acum": t}))
    if not frames:
        return
    comp = pd.concat(frames, axis=1).fillna(method="ffill").dropna(how="all")
    ax = comp.plot(title="Retorno acumulado comparado", figsize=(11, 4))
    ax.set_xlabel("Data"); ax.set_ylabel("Retorno acumulado")
    pdf.savefig(ax.figure); plt.close(ax.figure)

def add_summary(pdf: PdfPages, dfs: Dict[str, pd.DataFrame]):
    lines = []
    for t, d in dfs.items():
        if "close" in d.columns and len(d["close"]) > 0:
            first = d["close"].iloc[0]
            last  = d["close"].iloc[-1]
            total_ret = (last / first) - 1.0 if first != 0 else 0.0
            max_close = float(d["close"].max())
            min_close = float(d["close"].min())
            lines.append(f"{t}: Retorno = {total_ret: .2%} | Máx = {max_close:.2f} | Mín = {min_close:.2f} | N={len(d)}")
        else:
            lines.append(f"{t}: sem série 'close' válida.")
    text = "\n".join(lines) if lines else "Sem dados."
    fig = plt.figure(figsize=(11, 8.5))
    plt.axis("off")
    plt.text(0.5, 0.7, "Sumário", ha="center", va="center", fontsize=18, fontweight="bold")
    plt.text(0.1, 0.55, text, ha="left", va="center", fontsize=12, family="monospace")
    pdf.savefig(fig); plt.close(fig)

def build_pdf(dfs: Dict[str, pd.DataFrame], out_pdf: str, titulo: str = "Relatório Financeiro Local"):
    with PdfPages(out_pdf) as pdf:
        _page_title(pdf, titulo)
        plot_per_ticker(pdf, dfs)
        plot_comparison(pdf, dfs)
        add_summary(pdf, dfs)
