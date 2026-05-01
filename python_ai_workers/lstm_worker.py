# -*- coding: utf-8 -*-
"""
lstm_worker.py — LSTM Price Prediction Engine | Port 8004
Χρησιμοποιεί scikit-learn MinMaxScaler + Keras LSTM.
Δέχεται series από close prices, επιστρέφει N-step prediction.
"""

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)

# Lazy import Keras ώστε να μην κρασάρει αν δεν έχει GPU
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from sklearn.preprocessing import MinMaxScaler
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("[LSTM WORKER] WARNING: TensorFlow/Keras not installed. /predict will return mock.")


# ─────────────────────────────────────────────
# LSTM MODEL BUILDER
# ─────────────────────────────────────────────

def build_model(look_back: int) -> "Sequential":
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(look_back, 1)),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def prepare_sequences(data: np.ndarray, look_back: int):
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i - look_back:i, 0])
        y.append(data[i, 0])
    return np.array(X).reshape(-1, look_back, 1), np.array(y)


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict():
    """
    Body: { "prices": [2300.1, 2305.3, ...], "steps": 5 }
    Επιστρέφει: { "predictions": [...], "confidence": "..." }
    """
    data = request.get_json()
    prices = data.get("prices", [])
    steps = int(data.get("steps", 5))
    look_back = int(data.get("look_back", 20))
    epochs = int(data.get("epochs", 30))

    if len(prices) < look_back + 10:
        return jsonify({
            "error": f"Need at least {look_back + 10} prices. Got {len(prices)}."
        }), 400

    if not KERAS_AVAILABLE:
        # Mock response για dev environment χωρίς TensorFlow
        last = float(prices[-1])
        mock_predictions = [round(last * (1 + np.random.uniform(-0.005, 0.008)), 4)
                            for _ in range(steps)]
        return jsonify({
            "predictions": mock_predictions,
            "confidence": "LOW — Mock mode (TensorFlow not installed)",
            "note": "Install tensorflow to enable real LSTM predictions."
        })

    try:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(np.array(prices).reshape(-1, 1))

        X, y = prepare_sequences(scaled, look_back)

        model = build_model(look_back)
        model.fit(X, y, epochs=epochs, batch_size=16, verbose=0)

        # Παράγουμε N predictions (rolling)
        predictions_scaled = []
        input_seq = scaled[-look_back:].copy()

        for _ in range(steps):
            x_input = input_seq.reshape(1, look_back, 1)
            pred = model.predict(x_input, verbose=0)[0][0]
            predictions_scaled.append(pred)
            input_seq = np.append(input_seq[1:], [[pred]], axis=0)

        predictions = scaler.inverse_transform(
            np.array(predictions_scaled).reshape(-1, 1)
        ).flatten().tolist()

        # Confidence: inverse of recent volatility
        recent_vol = float(np.std(prices[-30:]) / np.mean(prices[-30:]) * 100)
        if recent_vol < 0.5:
            confidence = "HIGH"
        elif recent_vol < 1.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW — High volatility environment"

        return jsonify({
            "predictions": [round(p, 4) for p in predictions],
            "steps": steps,
            "confidence": confidence,
            "recent_volatility_pct": round(recent_vol, 3),
            "model": "LSTM (64→32 units)",
            "look_back": look_back,
        })

    except Exception as e:
        return jsonify({"error": f"LSTM failure: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "lstm_worker",
        "port": 8004,
        "keras_available": KERAS_AVAILABLE,
    })


if __name__ == "__main__":
    print("[LSTM ENGINE] Starting on port 8004...")
    app.run(host="127.0.0.1", port=8004, debug=False, use_reloader=False)
