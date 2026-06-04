from flask import Flask, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(
    filename="../logs/payment-service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

@app.route("/payment", methods=["POST"])
def payment():

    logging.info("Payment completed")

    return jsonify({
        "status": "success"
    })

if __name__ == "__main__":
    app.run(port=5002)