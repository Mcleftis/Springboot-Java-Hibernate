import numpy as np
import pandas as pd
import yfinance as yf
from statsmodels.tsa.stattools import coint


MACRO_TICKERS = {
    "DXY": "DX-Y.NYB",
    "US10Y": "^TNX",
    "VIX": "^VIX",
    "GOLD": "GC=F",
    "SP500": "^GSPC",
}


def fetch_series(ticker, period="2y"):
    data = yf.Ticker(ticker).history(period=period)
    if data.empty:
        return None
    return data["Close"]


def align(series_a, series_b):
    df = pd.concat([series_a, series_b], axis=1, join="inner").dropna()
    df.columns = ["a", "b"]
    return df


def correlation_analysis(asset_ticker="GC=F", period="2y"):
    asset = fetch_series(asset_ticker, period)
    if asset is None:
        return {"error": f"could not fetch {asset_ticker}"}
    results = {}
    for name, tk in MACRO_TICKERS.items():
        if tk == asset_ticker:
            continue
        macro = fetch_series(tk, period)
        if macro is None:
            results[name] = {"error": "fetch failed"}
            continue
        df = align(asset, macro)
        if len(df) < 30:
            results[name] = {"error": "insufficient overlap"}
            continue
        pearson = float(df["a"].corr(df["b"]))
        spearman = float(df["a"].corr(df["b"], method="spearman"))
        roll = df["a"].rolling(60).corr(df["b"])
        try:
            score, pval, _ = coint(df["a"], df["b"])
            cointegrated = bool(pval < 0.05)
        except Exception:
            pval, cointegrated = None, None
        results[name] = {
            "pearson": pearson,
            "spearman": spearman,
            "rolling_corr_last": float(roll.iloc[-1]) if not np.isnan(roll.iloc[-1]) else None,
            "coint_pvalue": float(pval) if pval is not None else None,
            "cointegrated": cointegrated,
        }
    return results


def institutional_signal(asset_ticker="GC=F", period="1y"):
    asset = fetch_series(asset_ticker, period)
    dxy = fetch_series("DX-Y.NYB", period)
    if asset is None or dxy is None:
        return {"error": "fetch failed"}
    df = align(asset, dxy)
    asset_chg = df["a"].pct_change(20).iloc[-1] * 100
    dxy_chg = df["b"].pct_change(20).iloc[-1] * 100
    signal_txt = "neutral"
    note = ""
    if asset_chg < -2 and dxy_chg < 0:
        signal_txt = "bullish_divergence"
        note = "Asset falling while DXY also falling - potential retail trap, institutional accumulation"
    elif asset_chg > 2 and dxy_chg > 0:
        signal_txt = "bearish_divergence"
        note = "Asset rising with DXY rising - unusual, watch for reversal"
    elif asset_chg < 0 and dxy_chg > 0:
        signal_txt = "confirmed_downtrend"
        note = "Asset down, Dollar up - textbook inverse correlation holding"
    else:
        signal_txt = "confirmed_uptrend"
        note = "Asset up, Dollar down - textbook inverse correlation holding"
    return {
        "asset_20d_change_pct": float(asset_chg),
        "dxy_20d_change_pct": float(dxy_chg),
        "signal": signal_txt,
        "interpretation": note,
    }


if __name__ == "__main__":
    import json
    import sys
    asset = sys.argv[1] if len(sys.argv) > 1 else "GC=F"
    out = {
        "correlations": correlation_analysis(asset),
        "institutional_signal": institutional_signal(asset),
    }
    print(json.dumps(out, indent=2, default=str))
