from __future__ import annotations
import argparse
from pathlib import Path
import sys

from finance_agent.core import FetchConfig, fetch_history, BrapiError
from finance_agent.report import build_pdf

def parse_args():
    p = argparse.ArgumentParser(
        description="Agente Financeiro Local (brapi.dev) → Gera PDF com histórico e indicadores."
    )
    p.add_argument("--tickers", nargs="+", required=True, help="Lista de tickers (ex.: PETR4 VALE3)")
    p.add_argument("--range", default="1y", help="Período do histórico (ex.: 1mo, 3mo, 1y, ytd, max)")
    p.add_argument("--interval", default="1d", help="Granularidade (ex.: 1d, 1wk, 1mo, 1m, 5m, 1h)")
    p.add_argument("--token", default=None, help="Token brapi.dev (opcional se usar tickers de teste)")
    p.add_argument("--out", default="output/relatorio.pdf", help="Caminho do PDF de saída")
    return p.parse_args()

def main():
    args = parse_args()

    try:
        cfg = FetchConfig(
            tickers=args.tickers,
            range=args.range,
            interval=args.interval,
            token=args.token
        )
        dfs = fetch_history(cfg)
        for t, df in dfs.items():
            print(f"[OK] {t}: linhas={len(df)} de {df['date'].min().date()} a {df['date'].max().date()}")
    except BrapiError as e:
        print(f"[ERRO] brapi: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO] inesperado: {e}", file=sys.stderr)
        sys.exit(2)

    out_pdf = Path(args.out)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(dfs, str(out_pdf), titulo=f"Relatório Financeiro Local — brapi.dev ({args.range}/{args.interval})")
    print(f"[FEITO] PDF gerado em: {out_pdf.resolve()}")

if __name__ == "__main__":
    main()
