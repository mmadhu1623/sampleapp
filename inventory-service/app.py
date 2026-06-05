from flask import Flask, jsonify, Response
import logging
import random
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

logging.basicConfig(
    filename="../logs/inventory-service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Prometheus metrics
REQUEST_COUNT = Counter('inventory_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
ERROR_COUNT = Counter('inventory_errors_total', 'Total errors', ['error_type'])
REQUEST_LATENCY = Histogram('inventory_request_latency_seconds', 'Request latency')

@app.route("/inventory/<item>")
def inventory(item):
    start = time.time()
    logging.info(f"Checking inventory for {item}")

    failure = random.choice([True, False])

    if failure:
        logging.error("Database Connection Timeout")
        logging.error("ConnectionPoolExhausted")
        REQUEST_COUNT.labels('GET', '/inventory', '500').inc()
        ERROR_COUNT.labels('ConnectionPoolExhausted').inc()
        ERROR_COUNT.labels('DatabaseConnectionTimeout').inc()
        REQUEST_LATENCY.observe(time.time() - start)
        return jsonify({
            "status": "error",
            "message": "Inventory DB unavailable"
        }), 500

    REQUEST_COUNT.labels('GET', '/inventory', '200').inc()
    REQUEST_LATENCY.observe(time.time() - start)
    return jsonify({
        "item": item,
        "stock": 10
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)