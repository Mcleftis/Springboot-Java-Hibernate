# -*- coding: utf-8 -*-
"""
quant_worker.py — Quant Engine | Port 8003
Indicators: RSI, MACD, ATR, Volume Profile, Order Blocks, Fair Value Gaps, Wyckoff (με Volume)
"""

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─────────────────────────────────────────────
# CORE INDICATOR FUNCTIONS (Vectorized / Pandas)
# ─────────────────────────────────────────────

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range — αντικαθιστά τα Bollinger Bands."""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()


# ─────────────────────────────────────────────
# VOLUME PROFILE — Point of Control (POC)
# ─────────────────────────────────────────────

def compute_volume_profile(df: pd.DataFrame, bins: int = 30) -> dict:
    """
    Υπολογίζει POC, Value Area High/Low.
    ΑΠΑΙΤΕΙ πραγματικό volume — όχι μηδέν.
    """
    if df["volume"].sum() == 0:
        return {"error": "Volume is zero. Provide real volume data."}

    price_min = df["low"].min()
    price_max = df["high"].max()
    price_bins = np.linspace(price_min, price_max, bins + 1)
    volume_at_price = np.zeros(bins)

    for _, row in df.iterrows():
        # Κατανέμουμε το volume στα price bins που αγγίζει το candle
        bin_indices = np.where(
            (price_bins[:-1] <= row["high"]) & (price_bins[1:] >= row["low"])
        )[0]
        if len(bin_indices) > 0:
            vol_per_bin = row["volume"] / len(bin_indices)
            volume_at_price[bin_indices] += vol_per_bin

    poc_idx = int(np.argmax(volume_at_price))
    poc_price = float((price_bins[poc_idx] + price_bins[poc_idx + 1]) / 2)

    # Value Area: 70% του συνολικού volume γύρω από το POC
    total_vol = volume_at_price.sum()
    target = total_vol * 0.70
    accumulated = volume_at_price[poc_idx]
    low_idx, high_idx = poc_idx, poc_idx

    while accumulated < target and (low_idx > 0 or high_idx < bins - 1):
        add_low = volume_at_price[low_idx - 1] if low_idx > 0 else 0
        add_high = volume_at_price[high_idx + 1] if high_idx < bins - 1 else 0
        if add_high >= add_low and high_idx < bins - 1:
            high_idx += 1
            accumulated += volume_at_price[high_idx]
        elif low_idx > 0:
            low_idx -= 1
            accumulated += volume_at_price[low_idx]
        else:
            break

    return {
        "poc": round(poc_price, 4),
        "value_area_high": round(float(price_bins[high_idx + 1]), 4),
        "value_area_low": round(float(price_bins[low_idx]), 4),
    }


# ─────────────────────────────────────────────
# ORDER BLOCKS — Institutional Buy/Sell Zones
# ─────────────────────────────────────────────

def find_order_blocks(df: pd.DataFrame, lookback: int = 5) -> list:
    """
    Order Block = Η τελευταία αντίθετη κίνηση πριν από ένα ισχυρό breakout.
    Bullish OB: Bearish candle → strong bullish move ακολουθεί.
    Bearish OB: Bullish candle → strong bearish move ακολουθεί.
    """
    obs = []
    closes = df["close"].values
    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values

    for i in range(1, len(df) - lookback):
        # Bullish Order Block
        if opens[i] > closes[i]:  # Bearish candle
            future_move = closes[i + lookback] - closes[i]
            candle_range = abs(opens[i] - closes[i])
            if future_move > candle_range * 2:  # Ισχυρό bullish follow-through
                obs.append({
                    "type": "BULLISH_OB",
                    "index": int(i),
                    "zone_high": round(float(opens[i]), 4),
                    "zone_low": round(float(closes[i]), 4),
                    "strength": round(float(future_move / candle_range), 2),
                })

        # Bearish Order Block
        if closes[i] > opens[i]:  # Bullish candle
            future_move = closes[i] - closes[i + lookback]
            candle_range = abs(closes[i] - opens[i])
            if future_move > candle_range * 2:  # Ισχυρό bearish follow-through
                obs.append({
                    "type": "BEARISH_OB",
                    "index": int(i),
                    "zone_high": round(float(closes[i]), 4),
                    "zone_low": round(float(opens[i]), 4),
                    "strength": round(float(future_move / candle_range), 2),
                })

    # Επιστρέφουμε τα 5 πιο ισχυρά
    obs.sort(key=lambda x: x["strength"], reverse=True)
    return obs[:5]


# ─────────────────────────────────────────────
# FAIR VALUE GAPS (FVG) — Institutional Imbalances
# ─────────────────────────────────────────────

def find_fair_value_gaps(df: pd.DataFrame) -> list:
    """
    FVG: Κενό ανάμεσα στο High του candle[i-1] και το Low του candle[i+1].
    Η αγορά γυρνάει σαν μαγνήτης να τα γεμίσει.
    """
    fvgs = []
    highs = df["high"].values
    lows = df["low"].values

    for i in range(1, len(df) - 1):
        # Bullish FVG: Low[i+1] > High[i-1]
        if lows[i + 1] > highs[i - 1]:
            fvgs.append({
                "type": "BULLISH_FVG",
                "index": int(i),
                "gap_low": round(float(highs[i - 1]), 4),
                "gap_high": round(float(lows[i + 1]), 4),
                "gap_size": round(float(lows[i + 1] - highs[i - 1]), 4),
            })
        # Bearish FVG: High[i+1] < Low[i-1]
        if highs[i + 1] < lows[i - 1]:
            fvgs.append({
                "type": "BEARISH_FVG",
                "index": int(i),
                "gap_high": round(float(lows[i - 1]), 4),
                "gap_low": round(float(highs[i + 1]), 4),
                "gap_size": round(float(lows[i - 1] - highs[i + 1]), 4),
            })

    fvgs.sort(key=lambda x: x["gap_size"], reverse=True)
    return fvgs[:5]


# ─────────────────────────────────────────────
# WYCKOFF — Σωστή υλοποίηση με Volume
# ─────────────────────────────────────────────

def wyckoff_phase(df: pd.DataFrame) -> dict:
    """
    Πραγματικό Wyckoff: Ψάχνει Springs, Upthrusts και Volume Climaxes.
    ΟΧΙ απλό last > first comparison.
    """
    if len(df) < 30:
        return {"error": "Need at least 30 candles for Wyckoff analysis."}

    closes = df["close"]
    volumes = df["volume"]
    highs = df["high"]
    lows = df["low"]

    recent = df.tail(30).copy()
    price_range_high = recent["high"].max()
    price_range_low = recent["low"].min()
    price_range = price_range_high - price_range_low

    avg_vol = volumes.mean()
    last_price = float(closes.iloc[-1])

    # Selling Climax (SC): Μεγάλος όγκος + πτώση τιμής κοντά σε low
    vol_climax = recent["volume"].max()
    climax_candle = recent.loc[recent["volume"] == vol_climax].iloc[0]
    is_selling_climax = (
        climax_candle["close"] < climax_candle["open"]
        and climax_candle["low"] <= price_range_low * 1.01
    )

    # Spring: Η τιμή βυθίζεται κάτω από το range_low με ΜΙΚΡΟ volume → fake breakdown
    recent_lows = recent.tail(10)
    spring_candidates = recent_lows[
        (recent_lows["low"] < price_range_low)
        & (recent_lows["volume"] < avg_vol * 0.8)
    ]
    has_spring = len(spring_candidates) > 0

    # Upthrust: Η τιμή ανεβαίνει πάνω από range_high αλλά κλείνει μέσα → fake breakout
    upthrust_candidates = recent[
        (recent["high"] > price_range_high)
        & (recent["close"] < price_range_high)
    ]
    has_upthrust = len(upthrust_candidates) > 0

    # Phase Logic
    if is_selling_climax and has_spring:
        phase = "ACCUMULATION"
        signal = "BULLISH_BIAS — Spring confirmed. Look for Sign of Strength."
    elif has_upthrust:
        phase = "DISTRIBUTION"
        signal = "BEARISH_BIAS — Upthrust detected. Institutional selling likely."
    elif last_price > price_range_high * 0.95:
        phase = "MARKUP"
        signal = "TREND_UP — Price breaking out of range on volume."
    elif last_price < price_range_low * 1.05:
        phase = "MARKDOWN"
        signal = "TREND_DOWN — Price breaking down of range."
    else:
        phase = "RANGING"
        signal = "NO_BIAS — Price inside range. Wait for Spring or Upthrust."

    return {
        "phase": phase,
        "signal": signal,
        "range_high": round(price_range_high, 4),
        "range_low": round(price_range_low, 4),
        "has_spring": has_spring,
        "has_upthrust": has_upthrust,
        "selling_climax_detected": bool(is_selling_climax),
    }


# ─────────────────────────────────────────────
# SWING HIGH / LOW — Liquidity Pools
# ─────────────────────────────────────────────

def find_liquidity_pools(df: pd.DataFrame, window: int = 5) -> dict:
    """
    Swing Highs = όπου μαζεύονται τα sell stop-losses του retail.
    Swing Lows  = όπου μαζεύονται τα buy stop-losses του retail.
    Αυτά είναι οι ζώνες που στοχεύουν οι τράπεζες.
    """
    highs = df["high"].values
    lows = df["low"].values

    swing_highs = []
    swing_lows = []

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i - window: i + window + 1]):
            swing_highs.append(round(float(highs[i]), 4))
        if lows[i] == min(lows[i - window: i + window + 1]):
            swing_lows.append(round(float(lows[i]), 4))

    return {
        "liquidity_highs": sorted(set(swing_highs), reverse=True)[:5],
        "liquidity_lows": sorted(set(swing_lows))[:5],
    }


# ─────────────────────────────────────────────
# FLASK ENDPOINTS
# ─────────────────────────────────────────────

def parse_dataframe(data: dict) -> pd.DataFrame:
    """Κοινή συνάρτηση parsing για όλα τα endpoints."""
    prices = data.get("prices", [])
    if not prices:
        raise ValueError("No prices provided.")

    if isinstance(prices[0], dict):
        df = pd.DataFrame(prices)
        for col in ["open", "high", "low", "close"]:
            if col not in df.columns:
                df[col] = df.get("close", 0)
        if "volume" not in df.columns:
            df["volume"] = 0
    else:
        # Simple list of close prices
        df = pd.DataFrame({
            "close": prices,
            "open": prices,
            "high": prices,
            "low": prices,
            "volume": [0] * len(prices),
        })

    df = df.astype({
        "open": float, "high": float, "low": float,
        "close": float, "volume": float
    })
    return df


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Κεντρικό endpoint. Δέχεται OHLCV δεδομένα.
    Επιστρέφει: RSI, MACD, ATR, Volume Profile, Order Blocks, FVGs, Wyckoff, Liquidity Pools.
    """
    data = request.get_json()
    symbol = data.get("symbol", "UNKNOWN")

    try:
        df = parse_dataframe(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if len(df) < 26:
        return jsonify({"error": "Need at least 26 candles for full analysis."}), 400

    # Indicators
    rsi_series = compute_rsi(df["close"])
    macd_line, signal_line, histogram = compute_macd(df["close"])
    atr_series = compute_atr(df)

    last_rsi = round(float(rsi_series.iloc[-1]), 2) if not rsi_series.isna().all() else None
    last_macd = round(float(macd_line.iloc[-1]), 4) if not macd_line.isna().all() else None
    last_signal = round(float(signal_line.iloc[-1]), 4) if not signal_line.isna().all() else None
    last_hist = round(float(histogram.iloc[-1]), 4) if not histogram.isna().all() else None
    last_atr = round(float(atr_series.iloc[-1]), 4) if not atr_series.isna().all() else None

    # RSI Signal
    if last_rsi is not None:
        if last_rsi > 70:
            rsi_signal = "OVERBOUGHT"
        elif last_rsi < 30:
            rsi_signal = "OVERSOLD"
        else:
            rsi_signal = "NEUTRAL"
    else:
        rsi_signal = "N/A"

    # MACD Signal
    if last_hist is not None:
        macd_signal = "BULLISH" if last_hist > 0 else "BEARISH"
    else:
        macd_signal = "N/A"

    result = {
        "symbol": symbol,
        "candles_analyzed": len(df),
        "current_price": round(float(df["close"].iloc[-1]), 4),
        "indicators": {
            "rsi": {"value": last_rsi, "signal": rsi_signal},
            "macd": {
                "macd_line": last_macd,
                "signal_line": last_signal,
                "histogram": last_hist,
                "signal": macd_signal,
            },
            "atr": {"value": last_atr, "note": "Volatility measure. Higher = more volatile."},
        },
        "smart_money": {
            "volume_profile": compute_volume_profile(df) if df["volume"].sum() > 0 else {"note": "No volume data"},
            "order_blocks": find_order_blocks(df),
            "fair_value_gaps": find_fair_value_gaps(df),
            "liquidity_pools": find_liquidity_pools(df),
        },
        "wyckoff": wyckoff_phase(df),
    }

    return jsonify(result)


@app.route("/wyckoff-full", methods=["POST"])
def wyckoff_full():
    """Endpoint συμβατό με το MarketDataController.java."""
    data = request.get_json()
    try:
        df = parse_dataframe(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    wyckoff = wyckoff_phase(df)
    liquidity = find_liquidity_pools(df)
    obs = find_order_blocks(df)

    return jsonify({
        "symbol": data.get("symbol", "UNKNOWN"),
        "wyckoff": wyckoff,
        "liquidity_pools": liquidity,
        "order_blocks": obs,
    })


@app.route("/order-blocks", methods=["POST"])
def order_blocks_endpoint():
    data = request.get_json()
    try:
        df = parse_dataframe(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"order_blocks": find_order_blocks(df)})


@app.route("/volume-profile", methods=["POST"])
def volume_profile_endpoint():
    data = request.get_json()
    try:
        df = parse_dataframe(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(compute_volume_profile(df))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP", "service": "quant_worker", "port": 8003})


if __name__ == "__main__":
    print("[QUANT ENGINE] Starting on port 8003...")
    app.run(host="127.0.0.1", port=8003, debug=False, use_reloader=False)
