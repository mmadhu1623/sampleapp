from flask import Flask, jsonify
import requests
import logging

app = Flask(__name__)

logging.basicConfig(
    filename="../logs/order-service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

@app.route("/orders")
def create_order():

    order_id = "ORD-1001"

    logging.info(f"Creating order {order_id}")

    try:

        inventory = requests.get(
            "http://localhost:5001/inventory/pizza"
        )

        if inventory.status_code != 200:

            logging.error(
                "Inventory Service returned 500"
            )

            return jsonify({
                "status": "failed"
            }), 500

        requests.post(
            "http://localhost:5002/payment"
        )

        logging.info(
            f"Order {order_id} created successfully"
        )

        return jsonify({
            "status": "success"
        })

    except Exception as ex:

        logging.error(str(ex))

        return jsonify({
            "status": "failed"
        }), 500

if __name__ == "__main__":
    app.run(port=5000)