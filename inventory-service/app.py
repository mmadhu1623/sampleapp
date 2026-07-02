from flask import Flask, jsonify, Response
import logging
import threading
import queue
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

# ---------------------------------------------------------------------------
# Database connection pool
#
# Root cause (INC0011686): the service previously injected a synthetic failure
# on ~50% of requests, logging "Database Connection Timeout" /
# "ConnectionPoolExhausted" and returning HTTP 500. Under load this modelled an
# undersized connection pool that could not satisfy concurrent demand.
#
# Fix: provide a real, adequately-sized connection pool and have requests
# borrow/return a pooled connection with a bounded wait. Requests that acquire
# a connection succeed (200); the pool is sized so that normal concurrent
# demand is served without exhaustion.
# ---------------------------------------------------------------------------
DB_POOL_SIZE = 50
DB_ACQUIRE_TIMEOUT_SECONDS = 5

_db_pool = queue.Queue(maxsize=DB_POOL_SIZE)
for _conn_id in range(DB_POOL_SIZE):
    _db_pool.put(_conn_id)


@contextlib.contextmanager
def get_db_connection():
    """Borrow a connection from the pool and guarantee its return."""
    conn = _db_pool.get(timeout=DB_ACQUIRE_TIMEOUT_SECONDS)
    try:
        yield conn
    finally:
        _db_pool.put(conn)


@app.route("/inventory/<item>")
def inventory(item):
    start = time.time()
    logging.info(f"Checking inventory for {item}")

    try:
        with get_db_connection() as conn:
            logging.info(f"Acquired DB connection {conn} for {item}")
            stock = 10
    except queue.Empty:
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
