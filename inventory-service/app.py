from flask import Flask, jsonify, Response
import logging
import threading
import contextlib
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

# Bounded DB connection pool.
# Root cause of INC0011662: the connection pool was being exhausted, causing
# intermittent 'Database Connection Timeout' / 'ConnectionPoolExhausted' errors.
# A semaphore-backed pool with a bounded acquire timeout ensures requests wait
# briefly for a free connection and connections are always released, preventing
# leaks and unbounded exhaustion.
DB_POOL_SIZE = 20
DB_ACQUIRE_TIMEOUT_SECONDS = 5
_db_pool = threading.BoundedSemaphore(DB_POOL_SIZE)


@contextlib.contextmanager
def db_connection():
    acquired = _db_pool.acquire(timeout=DB_ACQUIRE_TIMEOUT_SECONDS)
    if not acquired:
        raise TimeoutError("ConnectionPoolExhausted")
    try:
        yield
    finally:
        # Always release the connection back to the pool to avoid leaks.
        _db_pool.release()


@app.route("/inventory/<item>")
def inventory(item):
    start = time.time()
    logging.info(f"Checking inventory for {item}")

    try:
        with db_connection():
            stock = 10
    except TimeoutError:
        logging.error("Database Connection Timeout")
        logging.error("ConnectionPoolExhausted")
        REQUEST_COUNT.labels('GET', '/inventory', '503').inc()
        ERROR_COUNT.labels('ConnectionPoolExhausted').inc()
        ERROR_COUNT.labels('DatabaseConnectionTimeout').inc()
        REQUEST_LATENCY.observe(time.time() - start)
        return jsonify({
            "status": "error",
            "message": "Inventory DB unavailable"
        }), 503

    REQUEST_COUNT.labels('GET', '/inventory', '200').inc()
    REQUEST_LATENCY.observe(time.time() - start)
    return jsonify({
        "item": item,
        "stock": stock
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
