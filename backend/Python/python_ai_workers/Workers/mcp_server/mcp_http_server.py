import os
import json
import logging
import pika
import yfinance as yf
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
metrics = PrometheusMetrics(app)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "quant_user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "fleetpass")
ANALYSIS_QUEUE = os.getenv("ANALYSIS_QUEUE", "analysis_queue")


def publish_to_queue(payload):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=ANALYSIS_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=ANALYSIS_QUEUE,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


@app.route("/price/<symbol>", methods=["GET"])
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return jsonify({"error": f"Symbol '{symbol}' invalid or delisted."}), 404
        price = round(float(hist["Close"].iloc[-1]), 2)
        return jsonify({"symbol": symbol.upper(), "current_price": price, "source": "Yahoo Finance"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history/<symbol>", methods=["GET"])
def get_history(symbol):
    period = request.args.get("period", "6mo")
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return jsonify({"error": f"Symbol '{symbol}' invalid or delisted."}), 404
        prices = [round(float(p), 2) for p in hist["Close"].tolist()]
        return jsonify({"symbol": symbol.upper(), "prices": prices, "count": len(prices)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ingest/<symbol>", methods=["POST"])
def ingest_symbol(symbol):
    period = request.args.get("period", "6mo")
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return jsonify({"error": f"Symbol '{symbol}' invalid or delisted."}), 404
        prices = [round(float(p), 2) for p in hist["Close"].tolist()]
        payload = {"symbol": symbol.upper(), "prices": prices, "steps": 5}
        publish_to_queue(payload)
        return jsonify({"status": "PUBLISHED", "symbol": symbol.upper(), "queue": ANALYSIS_QUEUE, "data_points": len(prices)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP", "service": "mcp-market-data", "port": 8005})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8005)
