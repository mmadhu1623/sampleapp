import time

LOG_FILE = "logs/inventory-service.log"

print("Monitoring started...")

while True:

    with open(LOG_FILE, "r") as file:

        data = file.read()

        if "ConnectionPoolExhausted" in data:

            print(
                "ALERT GENERATED -> Inventory Service Failure"
            )

    time.sleep(10)
