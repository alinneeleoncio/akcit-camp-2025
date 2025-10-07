from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import os
import requests
import pandas as pd

BRAPI_BASE = "https://brapi.dev/api/quote"

@dataclass
class FetchConfig:
    tickers: List[str]
    range: Optional[str] = "1y"      # ex: 1mo, 3mo, 1y, ytd, max
    interval: Optional[str] = "1d"   # ex: 1d, 1wk, 1mo (ou intraday: 1m,5m,1h)
    token: Optional[str] = None      # Authorization: Bearer <token>

class BrapiError(Exception):
    pass

def _build_headers(token: Optional[str]) -> Dict[str, str]:
    tok = token or os.getenv("BRAPI_TOKEN")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

def _fetch_quote_raw(cfg: FetchConfig) -> dict:
    tickers_path = ",".join(cfg.tickers)
    params = {}
    if cfg.range:
        params["range"] = cfg.range
    if cfg.interval:
        params["interval"] = cfg.interval

    headers = _build_headers(cfg.token)
    url = f"{BRAPI_BASE}/{tickers_path}"
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise BrapiError(f"HTTP {resp.status_code} ao chamar {url} -> {resp.text[:200]}")
    data = resp.json()
    if "results" not in data or not data["results"]:
        raise BrapiError("Resposta sem 'results' válida.")
    return data

def _historical_to_df(item: dict) -> pd.DataFrame:
    hist = item.get("historicalDataPrice") or item.get("historicalData")
    if hist:
        df = pd.DataFrame(hist)
        # data pode vir em epoch (s) ou ISO; tratar ambos
        if "date" in df.columns:
            try:
                df["date"] = pd.to_datetime(df["date"], unit="s", utc=True).dt.tz_localize(None)
            except Exception:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
        elif "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_localize(None)

        # garantir 'close'
        if "close" not in df.columns and "regularMarketPrice" in item:
            df["close"] = float(item["regularMarketPrice"])

        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        # manter colunas essenciais
        keep = ["date", "close"]
        keep = [c for c in keep if c in df.columns]
        return df[keep].copy()

    # fallback: sem histórico → um único ponto do preço atual
    last_time = item.get("regularMarketTime") or item.get("updatedAt")
    last_price = item.get("regularMarketPrice")
    df = pd.DataFrame([{
        "date": pd.to_datetime(last_time, errors="coerce"),
        "close": float(last_price) if last_price is not None else None
    }]).dropna(subset=["date"]).reset_index(drop=True)
    return df

def fetch_history(cfg: FetchConfig) -> Dict[str, pd.DataFrame]:
    data = _fetch_quote_raw(cfg)
    out: Dict[str, pd.DataFrame] = {}
    for item in data.get("results", []):
        sym = item.get("symbol") or item.get("ticker") or "UNKNOWN"
        df = _historical_to_df(item)
        if df.empty:
            continue

        # indicadores simples
        if "close" in df.columns:
            df["mm20"] = df["close"].rolling(20, min_periods=1).mean()
            df["mm50"] = df["close"].rolling(50, min_periods=1).mean()
            first = df["close"].iloc[0]
            df["ret_acum"] = (df["close"] / first) - 1.0 if first != 0 else 0.0
        else:
            df["mm20"] = None
            df["mm50"] = None
            df["ret_acum"] = 0.0

        out[sym] = df

    if not out:
        raise BrapiError("Nenhum dado histórico retornado.")
    return out
