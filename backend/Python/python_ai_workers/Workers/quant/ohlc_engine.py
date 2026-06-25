import numpy as np
import pandas as pd
import yfinance as yf


def fetch_ohlcv(ticker="GC=F", period="6mo", interval="1d"):
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        return None
    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    return df[["open", "high", "low", "close", "volume"]].reset_index(drop=True)


def fair_value_gaps(ohlc, lookback=200):
    df = ohlc.tail(lookback).reset_index(drop=True)
    gaps = []
    for i in range(2, len(df)):
        c1_high = df["high"].iloc[i - 2]
        c1_low = df["low"].iloc[i - 2]
        c3_high = df["high"].iloc[i]
        c3_low = df["low"].iloc[i]
        if c1_high < c3_low:
            gaps.append({"index": i, "type": "bullish", "gap_low": float(c1_high), "gap_high": float(c3_low)})
        elif c1_low > c3_high:
            gaps.append({"index": i, "type": "bearish", "gap_low": float(c3_high), "gap_high": float(c1_low)})
    return gaps[-15:]


def order_blocks(ohlc, lookback=200, move_threshold=0.02):
    df = ohlc.tail(lookback).reset_index(drop=True)
    blocks = []
    for i in range(1, len(df) - 1):
        body_move = (df["close"].iloc[i + 1] - df["open"].iloc[i + 1]) / df["open"].iloc[i + 1]
        is_down = df["close"].iloc[i] < df["open"].iloc[i]
        is_up = df["close"].iloc[i] > df["open"].iloc[i]
        if body_move > move_threshold and is_down:
            blocks.append({"index": i, "type": "bullish_ob",
                           "zone_low": float(df["low"].iloc[i]), "zone_high": float(df["high"].iloc[i])})
        elif body_move < -move_threshold and is_up:
            blocks.append({"index": i, "type": "bearish_ob",
                           "zone_low": float(df["low"].iloc[i]), "zone_high": float(df["high"].iloc[i])})
    return blocks[-10:]


def liquidity_sweep(ohlc, lookback=50):
    df = ohlc.tail(lookback).reset_index(drop=True)
    recent_high = df["high"].iloc[:-1].max()
    recent_low = df["low"].iloc[:-1].min()
    last = df.iloc[-1]
    sweep = None
    if last["high"] > recent_high and last["close"] < recent_high:
        sweep = {"type": "sell_side_sweep", "level": float(recent_high),
                 "note": "price swept highs then rejected - liquidity grab above"}
    elif last["low"] < recent_low and last["close"] > recent_low:
        sweep = {"type": "buy_side_sweep", "level": float(recent_low),
                 "note": "price swept lows then rejected - liquidity grab below"}
    return sweep if sweep else {"type": "none"}


def true_atr(ohlc, period=14):
    df = ohlc.copy()
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return {"atr": float(tr.rolling(period).mean().iloc[-1])}


def ohlcv_volume_profile(ohlc, bins=30, value_area_pct=0.70):
    df = ohlc.copy()
    typical = (df["high"] + df["low"] + df["close"]) / 3
    lo, hi = typical.min(), typical.max()
    edges = np.linspace(lo, hi, bins + 1)
    hist, _ = np.histogram(typical, bins=edges, weights=df["volume"])
    mids = (edges[:-1] + edges[1:]) / 2
    poc_idx = int(np.argmax(hist))
    return {"poc": float(mids[poc_idx]),
            "profile": [{"price": float(mids[i]), "volume": float(hist[i])} for i in range(len(hist))]}


def full_ohlc_analysis(ticker="GC=F", period="6mo"):
    ohlc = fetch_ohlcv(ticker, period)
    if ohlc is None:
        return {"error": f"could not fetch {ticker}"}
    return {
        "ticker": ticker,
        "fair_value_gaps": fair_value_gaps(ohlc),
        "order_blocks": order_blocks(ohlc),
        "liquidity_sweep": liquidity_sweep(ohlc),
        "true_atr": true_atr(ohlc),
        "volume_profile": ohlcv_volume_profile(ohlc),
    }


if __name__ == "__main__":
    import json
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "GC=F"
    print(json.dumps(full_ohlc_analysis(ticker), indent=2, default=str))
