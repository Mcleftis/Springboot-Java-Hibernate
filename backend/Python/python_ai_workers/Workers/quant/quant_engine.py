import numpy as np
import pandas as pd
from scipy import signal, stats
from scipy.fft import rfft, rfftfreq
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA


def load_price_series(csv_path, currency="USD"):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    series = df[currency].astype(str).str.replace(",", "", regex=False)
    series = pd.to_numeric(series, errors="coerce")
    out = pd.DataFrame({"date": df["Date"].values, "close": series.values})
    out = out.dropna(subset=["close"]).reset_index(drop=True)
    return out


def sma(close, period):
    return pd.Series(close).rolling(period).mean().values


def ema(close, period):
    return pd.Series(close).ewm(span=period, adjust=False).mean().values


def rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).values


def macd(close, fast=12, slow=26, sig=9):
    f = pd.Series(close).ewm(span=fast, adjust=False).mean()
    s = pd.Series(close).ewm(span=slow, adjust=False).mean()
    line = f - s
    signal_line = line.ewm(span=sig, adjust=False).mean()
    return {"macd": line.values, "signal": signal_line.values, "hist": (line - signal_line).values}


def bollinger(close, period=20, mult=2):
    m = pd.Series(close).rolling(period).mean()
    sd = pd.Series(close).rolling(period).std()
    return {"middle": m.values, "upper": (m + mult * sd).values, "lower": (m - mult * sd).values}


def atr_from_close(close, period=14):
    tr = pd.Series(close).diff().abs()
    return tr.rolling(period).mean().values


def stochastic(close, period=14):
    s = pd.Series(close)
    low = s.rolling(period).min()
    high = s.rolling(period).max()
    k = 100 * (s - low) / (high - low).replace(0, np.nan)
    return {"k": k.values, "d": k.rolling(3).mean().values}


def market_structure(close, lookback=10):
    s = pd.Series(close)
    highs = s.rolling(lookback, center=True).max() == s
    lows = s.rolling(lookback, center=True).min() == s
    swing_highs = s[highs].tolist()
    swing_lows = s[lows].tolist()
    trend = "undetermined"
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        hh = swing_highs[-1] > swing_highs[-2]
        hl = swing_lows[-1] > swing_lows[-2]
        lh = swing_highs[-1] < swing_highs[-2]
        ll = swing_lows[-1] < swing_lows[-2]
        if hh and hl:
            trend = "uptrend"
        elif lh and ll:
            trend = "downtrend"
        else:
            trend = "ranging"
    return {"trend": trend, "swing_highs": swing_highs[-5:], "swing_lows": swing_lows[-5:]}


def fibonacci_levels(close, lookback=120):
    window = close[-lookback:]
    hi = float(np.max(window))
    lo = float(np.min(window))
    diff = hi - lo
    return {
        "high": hi, "low": lo,
        "fib_236": hi - 0.236 * diff,
        "fib_382": hi - 0.382 * diff,
        "fib_500": hi - 0.500 * diff,
        "fib_618": hi - 0.618 * diff,
        "fib_786": hi - 0.786 * diff,
        "ote_zone": [hi - 0.79 * diff, hi - 0.62 * diff],
    }


def wyckoff_phase(close, lookback=60):
    window = pd.Series(close[-lookback:])
    ma = window.mean()
    last = window.iloc[-1]
    slope = np.polyfit(range(len(window)), window.values, 1)[0]
    vol = window.std() / ma
    if slope > 0 and last > ma:
        phase = "markup"
    elif slope < 0 and last < ma:
        phase = "markdown"
    elif abs(slope) < (ma * 0.0005) and last < ma:
        phase = "accumulation"
    else:
        phase = "distribution"
    return {"phase": phase, "slope": float(slope), "relative_volatility": float(vol)}


def detect_price_gaps(close, threshold_pct=2.0):
    s = pd.Series(close)
    pct = s.pct_change() * 100
    gaps = []
    for i in range(1, len(s)):
        if abs(pct.iloc[i]) >= threshold_pct:
            gaps.append({"index": i, "from": float(s.iloc[i-1]), "to": float(s.iloc[i]), "pct": float(pct.iloc[i])})
    return gaps[-10:]


def zscore_mean_reversion(close, period=20):
    s = pd.Series(close)
    m = s.rolling(period).mean()
    sd = s.rolling(period).std()
    z = (s - m) / sd
    last_z = float(z.iloc[-1]) if not np.isnan(z.iloc[-1]) else 0.0
    signal_txt = "neutral"
    if last_z > 2:
        signal_txt = "overbought_revert_down"
    elif last_z < -2:
        signal_txt = "oversold_revert_up"
    return {"zscore": last_z, "signal": signal_txt}


def hurst_exponent(close):
    s = np.asarray(close, dtype=float)
    if len(s) < 100:
        return {"hurst": None, "regime": "insufficient_data"}
    lags = range(2, 100)
    tau = [np.sqrt(np.std(np.subtract(s[lag:], s[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(list(lags)), np.log(tau), 1)
    h = poly[0] * 2.0
    regime = "trending" if h > 0.5 else "mean_reverting" if h < 0.5 else "random_walk"
    return {"hurst": float(h), "regime": regime}


def adf_stationarity(close):
    s = pd.Series(close).dropna()
    result = adfuller(s, autolag="AIC")
    return {"adf_stat": float(result[0]), "p_value": float(result[1]),
            "stationary": bool(result[1] < 0.05)}


def cointegration_test(series_a, series_b):
    a = pd.Series(series_a).dropna()
    b = pd.Series(series_b).dropna()
    n = min(len(a), len(b))
    score, pvalue, _ = coint(a.iloc[-n:], b.iloc[-n:])
    return {"coint_stat": float(score), "p_value": float(pvalue),
            "cointegrated": bool(pvalue < 0.05)}


def rolling_correlation(series_a, series_b, window=60):
    a = pd.Series(series_a)
    b = pd.Series(series_b)
    n = min(len(a), len(b))
    corr = a.iloc[-n:].reset_index(drop=True).rolling(window).corr(b.iloc[-n:].reset_index(drop=True))
    return {"last_correlation": float(corr.iloc[-1]) if not np.isnan(corr.iloc[-1]) else None,
            "mean_correlation": float(corr.mean())}


def garch_volatility(close):
    try:
        from arch import arch_model
        returns = pd.Series(close).pct_change().dropna() * 100
        am = arch_model(returns, vol="Garch", p=1, q=1)
        res = am.fit(disp="off")
        forecast = res.forecast(horizon=5)
        var = forecast.variance.values[-1]
        return {"available": True, "forecast_volatility": [float(np.sqrt(v)) for v in var]}
    except Exception as e:
        return {"available": False, "reason": str(e), "note": "pip install arch"}


def arima_forecast(close, steps=5, order=(5, 1, 0)):
    try:
        s = pd.Series(close).dropna()
        model = ARIMA(s, order=order)
        fit = model.fit()
        fc = fit.forecast(steps=steps)
        return {"available": True, "forecast": [float(x) for x in fc.values]}
    except Exception as e:
        return {"available": False, "reason": str(e)}


def fft_cycles(close, top_n=5):
    s = np.asarray(close, dtype=float)
    s = s - np.mean(s)
    yf = np.abs(rfft(s))
    xf = rfftfreq(len(s), d=1)
    idx = np.argsort(yf)[::-1]
    cycles = []
    for i in idx:
        if xf[i] > 0:
            period = 1.0 / xf[i]
            cycles.append({"period_days": float(period), "strength": float(yf[i])})
        if len(cycles) >= top_n:
            break
    return cycles


def seasonal_decomposition(price_df, period=252):
    try:
        s = pd.Series(price_df["close"].values, index=pd.to_datetime(price_df["date"]))
        if len(s) < 2 * period:
            return {"available": False, "reason": "need at least 2 full periods"}
        result = seasonal_decompose(s, model="additive", period=period, extrapolate_trend="freq")
        return {"available": True,
                "trend_last": float(result.trend.dropna().iloc[-1]),
                "seasonal_last": float(result.seasonal.dropna().iloc[-1]),
                "residual_std": float(result.resid.dropna().std())}
    except Exception as e:
        return {"available": False, "reason": str(e)}


def hilbert_cycle(close):
    s = np.asarray(close, dtype=float)
    s = s - np.mean(s)
    analytic = signal.hilbert(s)
    phase = np.unwrap(np.angle(analytic))
    inst_freq = np.diff(phase) / (2.0 * np.pi)
    valid = inst_freq[inst_freq > 0]
    if len(valid) == 0:
        return {"dominant_period": None}
    return {"dominant_period": float(1.0 / np.median(valid))}


def returns_series(close):
    return pd.Series(close).pct_change().dropna()


def sharpe_ratio(close, rf=0.0, periods=252):
    r = returns_series(close)
    excess = r - rf / periods
    if r.std() == 0:
        return 0.0
    return float(np.sqrt(periods) * excess.mean() / r.std())


def sortino_ratio(close, rf=0.0, periods=252):
    r = returns_series(close)
    downside = r[r < 0].std()
    if downside == 0 or np.isnan(downside):
        return 0.0
    return float(np.sqrt(periods) * (r.mean() - rf / periods) / downside)


def max_drawdown(close):
    s = pd.Series(close)
    cummax = s.cummax()
    dd = (s - cummax) / cummax
    return {"max_drawdown_pct": float(dd.min() * 100)}


def value_at_risk(close, confidence=0.95):
    r = returns_series(close)
    var = np.percentile(r, (1 - confidence) * 100)
    cvar = r[r <= var].mean()
    return {"var_pct": float(var * 100), "cvar_pct": float(cvar * 100), "confidence": confidence}


def kelly_criterion(close):
    r = returns_series(close)
    wins = r[r > 0]
    losses = r[r < 0]
    if len(wins) == 0 or len(losses) == 0:
        return {"kelly_fraction": 0.0}
    win_rate = len(wins) / len(r)
    avg_win = wins.mean()
    avg_loss = abs(losses.mean())
    b = avg_win / avg_loss if avg_loss != 0 else 0
    kelly = win_rate - (1 - win_rate) / b if b != 0 else 0
    return {"kelly_fraction": float(max(0, min(kelly, 1))), "win_rate": float(win_rate)}


def monte_carlo(close, days=30, sims=1000):
    r = returns_series(close)
    mu = r.mean()
    sigma = r.std()
    last = float(close[-1])
    finals = []
    for _ in range(sims):
        path = last * np.cumprod(1 + np.random.normal(mu, sigma, days))
        finals.append(path[-1])
    finals = np.array(finals)
    return {"expected": float(np.mean(finals)),
            "p5": float(np.percentile(finals, 5)),
            "p50": float(np.percentile(finals, 50)),
            "p95": float(np.percentile(finals, 95))}


def backtest_sma_cross(close, fast=20, slow=50):
    s = pd.Series(close)
    f = s.rolling(fast).mean()
    sl = s.rolling(slow).mean()
    position = (f > sl).astype(int)
    r = s.pct_change()
    strat = position.shift(1) * r
    cum = (1 + strat.fillna(0)).cumprod()
    bench = (1 + r.fillna(0)).cumprod()
    trades = int(position.diff().abs().sum())
    return {"strategy_return_pct": float((cum.iloc[-1] - 1) * 100),
            "buy_hold_return_pct": float((bench.iloc[-1] - 1) * 100),
            "num_trades": trades,
            "sharpe": float(np.sqrt(252) * strat.mean() / strat.std()) if strat.std() > 0 else 0.0}


def full_analysis(price_df):
    close = price_df["close"].values
    return {
        "indicators": {
            "rsi_last": float(rsi(close)[-1]) if not np.isnan(rsi(close)[-1]) else None,
            "macd": {k: (float(v[-1]) if not np.isnan(v[-1]) else None) for k, v in macd(close).items()},
            "stochastic_k": float(stochastic(close)["k"][-1]) if not np.isnan(stochastic(close)["k"][-1]) else None,
        },
        "structure": market_structure(close),
        "wyckoff": wyckoff_phase(close),
        "fibonacci": fibonacci_levels(close),
        "price_gaps": detect_price_gaps(close),
        "mean_reversion": zscore_mean_reversion(close),
        "hurst": hurst_exponent(close),
        "stationarity": adf_stationarity(close),
        "cycles_fft": fft_cycles(close),
        "hilbert_cycle": hilbert_cycle(close),
        "seasonality": seasonal_decomposition(price_df),
        "arima": arima_forecast(close),
        "garch": garch_volatility(close),
        "risk": {
            "sharpe": sharpe_ratio(close),
            "sortino": sortino_ratio(close),
            "max_drawdown": max_drawdown(close),
            "var": value_at_risk(close),
            "kelly": kelly_criterion(close),
            "monte_carlo": monte_carlo(close),
        },
        "backtest_sma_cross": backtest_sma_cross(close),
        "unavailable_methods": {
            "reason": "require tick data or volume not present in OHLC-only dataset",
            "methods": ["CVD", "footprint_delta", "volume_profile", "vwap",
                        "order_book_imbalance", "absorption", "fair_value_gaps_ohlc",
                        "order_blocks_ohlc"],
            "data_source_needed": "Binance Futures aggTrades API for tick/volume data",
        },
    }


if __name__ == "__main__":
    import json
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "Daily.csv"
    currency = sys.argv[2] if len(sys.argv) > 2 else "USD"
    df = load_price_series(path, currency)
    print(f"Loaded {len(df)} rows for {currency}", file=sys.stderr)
    result = full_analysis(df)
    print(json.dumps(result, indent=2, default=str))
