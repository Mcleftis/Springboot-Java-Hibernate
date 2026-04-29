from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings("ignore")
app = FastAPI()
class PriceData(BaseModel):
    prices: List[float]
    symbol: str
class AIAnalysis(BaseModel):
    symbol: str
    predicted_next_price: float
    trend: str
    confidence: float
    cycle_position: float
    recommendation: str
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/analyze", response_model=AIAnalysis)
def analyze(data: PriceData):
    prices = np.array(data.prices)
    scaler = MinMaxScaler()
    prices_scaled = scaler.fit_transform(prices.reshape(-1, 1)).flatten()
    X = np.arange(len(prices)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, prices_scaled)
    next_index = np.array([[len(prices)]])
    next_scaled = model.predict(next_index)[0]
    next_price = scaler.inverse_transform([[next_scaled]])[0][0]
    slope = model.coef_[0]
    trend = "BULLISH" if slope > 0.001 else "BEARISH" if slope < -0.001 else "SIDEWAYS"
    confidence = max(0.0, model.score(X, prices_scaled))
    current_price = prices[-1]
    min_price = float(np.min(prices[-90:]))
    max_price = float(np.max(prices[-90:]))
    cycle_pos = (current_price - min_price) / (max_price - min_price) if max_price != min_price else 0.5
    if cycle_pos > 0.8 and trend == "BULLISH":
        rec = "NEAR_TOP - Consider reducing exposure"
    elif cycle_pos < 0.2 and trend == "BEARISH":
        rec = "NEAR_BOTTOM - Potential accumulation zone"
    elif trend == "BULLISH":
        rec = "UPTREND - Momentum positive"
    elif trend == "BEARISH":
        rec = "DOWNTREND - Caution advised"
    else:
        rec = "SIDEWAYS - Wait for breakout"
    return AIAnalysis(symbol=data.symbol, predicted_next_price=round(next_price, 2), trend=trend, confidence=round(confidence, 4), cycle_position=round(cycle_pos, 4), recommendation=rec)

@app.post("/wyckoff-full")
def wyckoff_full(data: PriceData):
    prices = np.array(data.prices)
    n = len(prices)
    if n < 50:
        return {"error": "Insufficient data"}
    events = []
    for i in range(2, n-2):
        drop = (prices[i] - prices[i-2]) / prices[i-2]
        if drop < -0.05:
            events.append({"event": "SELLING_CLIMAX", "index": i, "price": round(float(prices[i]), 2), "description": "Large sell-off detected. Possible institutional accumulation start."})
    for i in range(1, len(events)):
        if events[i-1]["event"] == "SELLING_CLIMAX":
            sc_index = events[i-1]["index"]
            for j in range(sc_index+1, min(sc_index+20, n)):
                rally = (prices[j] - prices[sc_index]) / prices[sc_index]
                if rally > 0.03:
                    events.append({"event": "AUTOMATIC_RALLY", "index": j, "price": round(float(prices[j]), 2), "description": "Price bounced after Selling Climax."})
                    break
    sc_events = [e for e in events if e["event"] == "SELLING_CLIMAX"]
    for sc in sc_events:
        sc_price = sc["price"]; sc_index = sc["index"]
        for j in range(sc_index+5, min(sc_index+40, n)):
            diff = abs(prices[j] - sc_price) / sc_price
            if diff < 0.02:
                events.append({"event": "SECONDARY_TEST", "index": j, "price": round(float(prices[j]), 2), "description": "Price retested Selling Climax level."})
                break
    for i in range(2, n-2):
        gain = (prices[i] - prices[i-2]) / prices[i-2]
        if gain > 0.04:
            events.append({"event": "SIGN_OF_STRENGTH", "index": i, "price": round(float(prices[i]), 2), "description": "Strong upward move. Institutions may be marking up."})
    sos_events = [e for e in events if e["event"] == "SIGN_OF_STRENGTH"]
    for sos in sos_events:
        sos_index = sos["index"]
        for j in range(sos_index+1, min(sos_index+15, n)):
            pullback = (prices[j] - prices[sos_index]) / prices[sos_index]
            if -0.03 < pullback < -0.01:
                events.append({"event": "LAST_POINT_OF_SUPPORT", "index": j, "price": round(float(prices[j]), 2), "description": "Final pullback before potential markup phase."})
                break
    last_price = float(prices[-1]); recent_high = float(np.max(prices[-30:])); recent_low = float(np.min(prices[-30:]))
    position = (last_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
    if position > 0.8: current_phase = "DISTRIBUTION - Institutions likely selling"
    elif position > 0.6: current_phase = "MARKUP - Price trending up"
    elif position > 0.4: current_phase = "TRANSITION - No clear phase"
    elif position > 0.2: current_phase = "ACCUMULATION - Institutions likely buying"
    else: current_phase = "MARKDOWN - Price trending down"
    recent_events = sorted(events, key=lambda x: x["index"], reverse=True)[:10]
    return {"symbol": data.symbol, "current_phase": current_phase, "cycle_position": round(position, 4), "total_events_detected": len(events), "recent_events": recent_events, "recommendation": f"Phase: {current_phase} | Last price: {round(last_price, 2)} | Cycle position: {round(position*100, 1)}%"}