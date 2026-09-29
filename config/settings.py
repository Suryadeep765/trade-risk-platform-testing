import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TRADES_TOPIC = "trades"
MARKET_TOPIC = "market_data"
RISK_TOPIC = "risk_metrics"
DB_PATH = os.getenv("RISK_DB_PATH", "data/risk.db")
SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA"]
RISK_FREE_RATE = 0.045
DEFAULT_VOL = 0.25
VAR_CONFIDENCE = 0.95
