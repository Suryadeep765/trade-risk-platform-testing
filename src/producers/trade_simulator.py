import json
import random
import time
import uuid

from confluent_kafka import Producer

from config.settings import KAFKA_BOOTSTRAP, TRADES_TOPIC, SYMBOLS


def main():
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP, "linger.ms": 2, "compression.type": "lz4"})
    while True:
        symbol = random.choice(SYMBOLS)
        asset_type = random.choices(["EQUITY", "OPTION"], weights=[0.65, 0.35])[0]
        quantity = random.choice([10, 25, 50, 100, 250]) * random.choice([-1, 1])
        price = {"AAPL": 225, "MSFT": 510, "NVDA": 185, "TSLA": 430}[symbol] * (1 + random.uniform(-0.01, 0.01))
        event = {
            "ts": time.time(),
            "trade_id": str(uuid.uuid4()),
            "symbol": symbol,
            "asset_type": asset_type,
            "quantity": quantity,
            "price": round(price, 4),
        }
        if asset_type == "OPTION":
            event.update({
                "strike": round(price * random.choice([0.9, 1.0, 1.1]), 2),
                "expiry_years": random.choice([0.08, 0.25, 0.5, 1.0]),
                "option_type": random.choice(["call", "put"]),
                "volatility": random.uniform(0.18, 0.45),
            })
        producer.produce(TRADES_TOPIC, key=symbol, value=json.dumps(event))
        producer.poll(0)
        producer.flush()
        time.sleep(random.uniform(0.05, 0.20))


if __name__ == "__main__":
    main()
