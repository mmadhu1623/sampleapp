from flask import Flask, jsonify, Response
import requests
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

logging.basicConfig(
    filename="../logs/order-service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

REQUEST_COUNT = Counter('order_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
ERROR_COUNT = Counter('order_errors_total', 'Total errors', ['error_type'])
REQUEST_LATENCY = Histogram('order_request_latency_seconds', 'Request latency')

@app.route("/orders")
def create_order():
    start = time.time()
    order_id = "ORD-1001"
    logging.info(f"Creating order {order_id}")

    try:
        inventory = requests.get("http://localhost:5001/inventory/pizza", timeout=5)

        if inventory.status_code != 200:
            logging.error("Inventory Service returned 500")
            REQUEST_COUNT.labels('GET', '/orders', '500').inc()
            ERROR_COUNT.labels('InventoryServiceError').inc()
            REQUEST_LATENCY.observe(time.time() - start)
            return jsonify({"status": "failed", "reason": "inventory_error"}), 500

        requests.post("http://localhost:5002/payment", timeout=5)

        logging.info(f"Order {order_id} created successfully")
        REQUEST_COUNT.labels('GET', '/orders', '200').inc()
        REQUEST_LATENCY.observe(time.time() - start)
        return jsonify({"status": "success", "order_id": order_id})

    except Exception as ex:
        logging.error(str(ex))
        REQUEST_COUNT.labels('GET', '/orders', '500').inc()
        ERROR_COUNT.labels('Exception').inc()
        REQUEST_LATENCY.observe(time.time() - start)
        return jsonify({"status": "failed"}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)