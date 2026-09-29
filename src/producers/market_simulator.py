import json
import random
import time
from datetime import datetime, timezone

import numpy as np
from confluent_kafka import Producer

from config.settings import KAFKA_BOOTSTRAP, MARKET_TOPIC, SYMBOLS

BASE = {"AAPL": 225.0, "MSFT": 510.0, "NVDA": 185.0, "TSLA": 430.0}


def main():
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP, "linger.ms": 2, "compression.type": "lz4"})
    prices = BASE.copy()
    while True:
        for symbol in SYMBOLS:
            shock = np.random.normal(0, 0.0015)
            if random.random() < 0.01:
                shock += np.random.normal(0, 0.012)
            prices[symbol] *= max(0.95, 1 + shock)
            event = {
                "ts": time.time(),
                "iso_ts": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "price": round(prices[symbol], 4),
                "volatility": 0.18 + abs(shock) * 8,
                "rate": 0.045,
            }
            producer.produce(MARKET_TOPIC, key=symbol, value=json.dumps(event))
        producer.poll(0)
        producer.flush()
        time.sleep(0.20)


if __name__ == "__main__":
    main()
