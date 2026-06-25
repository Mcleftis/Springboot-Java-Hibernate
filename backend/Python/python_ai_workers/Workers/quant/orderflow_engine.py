import requests
import numpy as np
import pandas as pd


BINANCE_AGG_URL = "https://api.binance.com/api/v3/aggTrades"
BINANCE_KLINE_URL = "https://api.binance.com/api/v3/klines"


def fetch_agg_trades(symbol="BTCUSDT", limit=1000):
    r = requests.get(BINANCE_AGG_URL, params={"symbol": symbol, "limit": limit}, timeout=10)
    r.raise_for_status()
    raw = r.json()
    rows = []
    for t in raw:
        rows.append({
            "price": float(t["p"]),
            "qty": float(t["q"]),
            "timestamp": int(t["T"]),
            "is_buyer_maker": bool(t["m"]),
        })
    df = pd.DataFrame(rows)
    df["side"] = np.where(df["is_buyer_maker"], "sell", "buy")
    df["signed_qty"] = np.where(df["side"] == "buy", df["qty"], -df["qty"])
    return df


def cumulative_volume_delta(trades_df):
    cvd = trades_df["signed_qty"].cumsum()
    return {
        "cvd_last": float(cvd.iloc[-1]),
        "cvd_series": [float(x) for x in cvd.values[-50:]],
        "total_buy_volume": float(trades_df[trades_df["side"] == "buy"]["qty"].sum()),
        "total_sell_volume": float(trades_df[trades_df["side"] == "sell"]["qty"].sum()),
    }


def delta_per_level(trades_df, bins=50):
    prices = trades_df["price"]
    lo, hi = prices.min(), prices.max()
    edges = np.linspace(lo, hi, bins + 1)
    trades_df = trades_df.copy()
    trades_df["bin"] = pd.cut(trades_df["price"], edges, include_lowest=True)
    grouped = trades_df.groupby("bin", observed=True).apply(
        lambda g: pd.Series({
            "buy_vol": g[g["side"] == "buy"]["qty"].sum(),
            "sell_vol": g[g["side"] == "sell"]["qty"].sum(),
        })
    )
    grouped["delta"] = grouped["buy_vol"] - grouped["sell_vol"]
    grouped["price_mid"] = [interval.mid for interval in grouped.index]
    out = []
    for _, row in grouped.iterrows():
        out.append({
            "price": float(row["price_mid"]),
            "buy_vol": float(row["buy_vol"]),
            "sell_vol": float(row["sell_vol"]),
            "delta": float(row["delta"]),
        })
    return out


def volume_profile(trades_df, bins=50, value_area_pct=0.70):
    prices = trades_df["price"]
    lo, hi = prices.min(), prices.max()
    edges = np.linspace(lo, hi, bins + 1)
    hist, _ = np.histogram(prices, bins=edges, weights=trades_df["qty"])
    mids = (edges[:-1] + edges[1:]) / 2
    poc_idx = int(np.argmax(hist))
    poc = float(mids[poc_idx])
    total = hist.sum()
    target = total * value_area_pct
    included = {poc_idx}
    acc = hist[poc_idx]
    lo_idx = hi_idx = poc_idx
    while acc < target and (lo_idx > 0 or hi_idx < len(hist) - 1):
        down = hist[lo_idx - 1] if lo_idx > 0 else -1
        up = hist[hi_idx + 1] if hi_idx < len(hist) - 1 else -1
        if up >= down:
            hi_idx += 1
            acc += hist[hi_idx]
            included.add(hi_idx)
        else:
            lo_idx -= 1
            acc += hist[lo_idx]
            included.add(lo_idx)
    va_prices = [mids[i] for i in included]
    return {
        "poc": poc,
        "vah": float(max(va_prices)),
        "val": float(min(va_prices)),
        "profile": [{"price": float(mids[i]), "volume": float(hist[i])} for i in range(len(hist))],
    }


def vwap(trades_df):
    pv = (trades_df["price"] * trades_df["qty"]).sum()
    v = trades_df["qty"].sum()
    return {"vwap": float(pv / v) if v > 0 else None}


def absorption_detection(trades_df, window=100):
    recent = trades_df.tail(window)
    price_range = recent["price"].max() - recent["price"].min()
    total_vol = recent["qty"].sum()
    price_move_pct = price_range / recent["price"].mean() * 100
    absorption = total_vol > trades_df["qty"].mean() * window * 1.5 and price_move_pct < 0.5
    return {
        "absorption_detected": bool(absorption),
        "volume": float(total_vol),
        "price_move_pct": float(price_move_pct),
        "note": "high volume with minimal price move - institutional absorption" if absorption else "normal",
    }


def full_orderflow(symbol="BTCUSDT", limit=1000):
    trades = fetch_agg_trades(symbol, limit)
    return {
        "symbol": symbol,
        "cvd": cumulative_volume_delta(trades),
        "volume_profile": volume_profile(trades),
        "vwap": vwap(trades),
        "delta_per_level": delta_per_level(trades),
        "absorption": absorption_detection(trades),
    }


if __name__ == "__main__":
    import json
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    print(json.dumps(full_orderflow(symbol), indent=2, default=str))
