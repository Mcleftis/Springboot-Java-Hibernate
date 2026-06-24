import os
import json
import time
import threading
import logging
import pika
import psycopg2

logging.basicConfig(level=logging.INFO)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "quant_user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "fleetpass")
ANALYSIS_QUEUE = os.getenv("ANALYSIS_QUEUE", "analysis_queue")
DB_URL = os.getenv("DB_URL", "postgresql://quant_user:fleetpass@postgres:5432/quantdb")
WORKER_NAME = os.getenv("WORKER_NAME", "worker")


def save_result(symbol, result_json):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS analysis_results ("
        "id SERIAL PRIMARY KEY, symbol VARCHAR(50), worker VARCHAR(50), "
        "result JSONB, created_at TIMESTAMP DEFAULT NOW())"
    )
    cur.execute(
        "INSERT INTO analysis_results (symbol, worker, result) VALUES (%s, %s, %s)",
        (symbol, WORKER_NAME, json.dumps(result_json)),
    )
    conn.commit()
    cur.close()
    conn.close()


def process_message(process_fn, ch, method, properties, body):
    try:
        data = json.loads(body)
        symbol = data.get("symbol", "UNKNOWN")
        logging.info(f"{WORKER_NAME} processing {symbol}")
        result = process_fn(data)
        save_result(symbol, result)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"{WORKER_NAME} completed {symbol}")
    except Exception as e:
        logging.error(f"{WORKER_NAME} failed: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer(process_fn):
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST, credentials=credentials, heartbeat=600
            )
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=ANALYSIS_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=ANALYSIS_QUEUE,
                on_message_callback=lambda ch, m, p, b: process_message(process_fn, ch, m, p, b),
            )
            logging.info(f"{WORKER_NAME} listening on {ANALYSIS_QUEUE}")
            channel.start_consuming()
        except Exception as e:
            logging.error(f"{WORKER_NAME} connection lost: {str(e)}. Retrying in 5s.")
            time.sleep(5)


def launch_consumer_thread(process_fn):
    t = threading.Thread(target=start_consumer, args=(process_fn,), daemon=True)
    t.start()
