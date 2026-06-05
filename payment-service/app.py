from flask import Flask, jsonify, Response
import logging
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

logging.basicConfig(
    filename="../logs/payment-service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

REQUEST_COUNT = Counter('payment_requests_total', 'Total requests', ['method', 'endpoint', 'status'])

@app.route("/payment", methods=["POST"])
def payment():
    logging.info("Payment completed")
    REQUEST_COUNT.labels('POST', '/payment', '200').inc()
    return jsonify({"status": "success"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)