from __future__ import annotations

import json
import math
import threading
import time
from collections import defaultdict, deque

import numpy as np
from confluent_kafka import Consumer, Producer
from sklearn.ensemble import IsolationForest

from config.settings import *
from src.models.risk import black_scholes, historical_var
from src.storage.state_store import StateStore


class RiskEngine:
    def __init__(self):
        self.positions = defaultdict(list)
        self.prices = {}
        self.return_history = defaultdict(lambda: deque(maxlen=500))
        self.store = StateStore(DB_PATH)
        self.producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP, "linger.ms": 2, "compression.type": "lz4"})
        self.anomaly_model = IsolationForest(contamination=0.03, random_state=42)
        self.anomaly_features = []
        self.last_snapshot = 0.0

    def consume(self, topics, group):
        c = Consumer({
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": group,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        })
        c.subscribe(topics)
        try:
            while True:
                msg = c.poll(1.0)
                if msg is None or msg.error():
                    continue
                event = json.loads(msg.value())
                if msg.topic() == TRADES_TOPIC:
                    self.handle_trade(event)
                else:
                    self.handle_market(event)
        finally:
            c.close()

    def handle_trade(self, e):
        self.positions[e["symbol"]].append(e)
        feature = [
            abs(e["quantity"] * e["price"]),
            abs(e["quantity"]),
            e["price"],
            abs(e.get("strike", e["price"]) - e["price"]) / max(e["price"], 1),
        ]
        self.anomaly_features.append(feature)
        self.store.add_event(e["ts"], "trade", e)

    def handle_market(self, e):
        symbol = e["symbol"]
        previous = self.prices.get(symbol)
        self.prices[symbol] = e["price"]
        if previous:
            self.return_history[symbol].append(e["price"] / previous - 1)
        now = time.time()
        if now - self.last_snapshot >= 1.0:
            self.publish_snapshot()
            self.last_snapshot = now

    def anomaly_count(self):
        if len(self.anomaly_features) < 50:
            return 0
        arr = np.asarray(self.anomaly_features[-500:])
        labels = self.anomaly_model.fit_predict(arr)
        return int((labels == -1).sum())

    def publish_snapshot(self):
        pnl = gross = net = delta = gamma = vega = theta = 0.0
        positions_out = []
        pnl_samples = []
        for symbol, trades in self.positions.items():
            spot = self.prices.get(symbol)
            if spot is None:
                continue
            for t in trades:
                qty = t["quantity"]
                entry = t["price"]
                if t["asset_type"] == "EQUITY":
                    value = qty * spot
                    trade_pnl = qty * (spot - entry)
                    d = qty
                    g = v = th = 0.0
                else:
                    price, od, g, v, th = black_scholes(
                        spot, t["strike"], t["expiry_years"], t.get("rate", RISK_FREE_RATE),
                        t.get("volatility", DEFAULT_VOL), t["option_type"]
                    )
                    value = qty * price * 100
                    trade_pnl = qty * (price - entry) * 100
                    d = qty * od * 100
                    g = qty * g * 100
                    v = qty * v * 100
                    th = qty * th * 100
                pnl += trade_pnl
                gross += abs(value)
                net += value
                delta += d
                gamma += g
                vega += v
                theta += th
                pnl_samples.append(trade_pnl)
                positions_out.append({"symbol": symbol, "type": t["asset_type"], "qty": qty, "value": value, "pnl": trade_pnl})
        # A portfolio-level historical approximation using recent per-symbol returns and current net exposure.
        simulated_pnl = []
        for symbol, returns in self.return_history.items():
            exposure = sum(t["quantity"] * t["price"] for t in self.positions.get(symbol, []) if t["asset_type"] == "EQUITY")
            simulated_pnl.extend(float(exposure * r) for r in returns)
        var95 = historical_var(simulated_pnl if simulated_pnl else pnl_samples, VAR_CONFIDENCE)
        snapshot = {
            "ts": time.time(), "pnl": pnl, "gross_exposure": gross, "net_exposure": net,
            "delta": delta, "gamma": gamma, "vega": vega, "theta": theta,
            "var95": var95, "anomaly_count": self.anomaly_count(), "positions": positions_out,
        }
        self.store.add_snapshot(snapshot)
        self.producer.produce(RISK_TOPIC, key="portfolio", value=json.dumps(snapshot))
        self.producer.poll(0)


def main():
    engine = RiskEngine()
    engine.consume([TRADES_TOPIC, MARKET_TOPIC], "risk-engine-v1")


if __name__ == "__main__":
    main()
