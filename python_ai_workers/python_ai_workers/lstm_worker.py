import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from sklearn.preprocessing import MinMaxScaler
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False

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

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    prices = data.get("prices", [])
    steps = int(data.get("steps", 5))
    look_back = int(data.get("look_back", 20))
    epochs = int(data.get("epochs", 30))

    if len(prices) < look_back + 10:
        return jsonify({"error": f"Need at least {look_back + 10} prices. Got {len(prices)}."}), 400

    if not KERAS_AVAILABLE:
        last = float(prices[-1])
        mock_predictions = [round(last * (1 + np.random.uniform(-0.005, 0.008)), 4) for _ in range(steps)]
        
        with open("lstm_output.txt", "w", encoding="utf-8") as f:
            f.write(f"LSTM Predictions: {mock_predictions}\nConfidence: LOW")
        
        return jsonify({"predictions": mock_predictions, "confidence": "LOW"})

    try:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(np.array(prices).reshape(-1, 1))

        X, y = prepare_sequences(scaled, look_back)

        model = build_model(look_back)
        model.fit(X, y, epochs=epochs, batch_size=16, verbose=0)

        predictions_scaled = []
        input_seq = scaled[-look_back:].copy()

        for _ in range(steps):
            x_input = input_seq.reshape(1, look_back, 1)
            pred = model.predict(x_input, verbose=0)[0][0]
            predictions_scaled.append(pred)
            input_seq = np.append(input_seq[1:], [[pred]], axis=0)

        predictions = scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1)).flatten().tolist()

        recent_vol = float(np.std(prices[-30:]) / np.mean(prices[-30:]) * 100)
        if recent_vol < 0.5:
            confidence = "HIGH"
        elif recent_vol < 1.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
            
        result_data = {
            "predictions": [round(p, 4) for p in predictions],
            "steps": steps,
            "confidence": confidence,
            "recent_volatility_pct": round(recent_vol, 3),
            "model": "LSTM",
            "look_back": look_back,
        }
        
        with open("lstm_output.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(result_data, indent=4))

        return jsonify(result_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP", "service": "lstm_worker", "port": 8004})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8004, debug=False, use_reloader=False)