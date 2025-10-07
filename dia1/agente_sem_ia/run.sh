cd finance_agent_local
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Prepare seus CSVs em: finance_agent_local/data/acoes/PETR4.csv etc.
python main.py --base-dir data/acoes --tickers PETR4 VALE3 --out output/relatorio.pdf --dt-ini 2024-01-01 --dt-fim 2024-12-31
