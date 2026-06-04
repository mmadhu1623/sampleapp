from flask import Flask, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(
    filename="../logs/inventory-service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

@app.route("/inventory/<item>")
def inventory(item):

    logging.info(f"Checking inventory for {item}")

    failure = random.choice([True, False])

    if failure:
        logging.error("Database Connection Timeout")
        logging.error("ConnectionPoolExhausted")

        return jsonify({
            "status": "error",
            "message": "Inventory DB unavailable"
        }), 500

    return jsonify({
        "item": item,
        "stock": 10
    })

if __name__ == "__main__":
    app.run(port=5001)