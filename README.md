# Real-Time Trade Risk & Analytics Platform

A local, event-driven portfolio risk platform that simulates trades and market prices, calculates mark-to-market P&L, exposure, Black-Scholes Greeks and historical VaR, detects anomalous trades, and renders a live Streamlit dashboard.

## Architecture

```text
                  ┌──────────────────┐
                  │ Trade Simulator  │
                  └────────┬─────────┘
                           │ trades
                           ▼
                    ┌──────────────┐
                    │    Kafka     │
                    │ trades topic │
                    └──────┬───────┘
                           │
                           │
┌──────────────────┐       ▼       ┌────────────────────┐
│ Market Simulator │──► market ──►│   Risk Engine      │
└──────────────────┘     topic     │ P&L / Greeks / VaR │
                                   │ anomaly detection  │
                                   └─────────┬──────────┘
                                             │ risk_metrics
                                             ▼
                                      ┌──────────────┐
                                      │    Kafka     │
                                      └──────┬───────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │ SQLite state │
                                      └──────┬───────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │  Streamlit   │
                                      │  Dashboard   │
                                      └──────────────┘
```

The design follows the separation between event producers, consumers/stream processors and materialized views that makes Kafka useful for real-time financial pipelines. It does **not** require GS Quant credentials.

## Features

- Simulated equity and European call/put trades
- Simulated market-price ticks with volatility shocks
- Kafka topics for `trades`, `market_data`, and `risk_metrics`
- Position aggregation and mark-to-market P&L
- Gross/net notional and delta exposure
- Black-Scholes price + delta, gamma, vega and theta
- Historical 95% one-day VaR using simulated return history
- Isolation Forest trade anomaly detection
- Persisted risk snapshots in SQLite
- Live Streamlit dashboard
- Unit tests for pricing, Greeks, VaR and P&L
- Benchmark script for throughput/latency measurement

## Tech stack

Python 3.11+, Apache Kafka-compatible broker (Redpanda in Docker), `confluent-kafka`, NumPy, pandas, scikit-learn, SciPy, Streamlit, Plotly, SQLite, pytest.

## Quick start

### 1. Create environment

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the broker

```bash
docker compose up -d
```

### 3. Start the risk engine

```bash
python -m src.engine.risk_engine
```

### 4. Start market + trade simulators in separate terminals

```bash
python -m src.producers.market_simulator
python -m src.producers.trade_simulator
```

### 5. Open dashboard

```bash
streamlit run dashboard/app.py
```

Dashboard: `http://localhost:8501`

### 6. Run tests

```bash
pytest -q
```

### 7. Run the benchmark

```bash
python -m src.benchmark
```

The benchmark prints the **measured** event throughput and processing latency on your machine. Do not put those numbers on your resume until you have actually run it.

## Project structure

```text
trade-risk-platform/
├── dashboard/app.py
├── src/
│   ├── benchmark.py
│   ├── engine/risk_engine.py
│   ├── models/risk.py
│   ├── producers/market_simulator.py
│   ├── producers/trade_simulator.py
│   └── storage/state_store.py
├── tests/
├── config/settings.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Risk methodology

### P&L

For each position:

`P&L = quantity × (current_price - entry_price)`

with short positions represented by negative quantity.

### Black-Scholes

For European options, the engine calculates theoretical value and first/second-order Greeks from spot, strike, time-to-expiry, volatility and risk-free rate.

### Historical VaR

For each snapshot, the engine applies the latest simulated return distribution to current portfolio exposure and reports the 5th percentile loss as 95% one-day historical VaR.

This is a **portfolio project implementation**, not a production regulatory VaR model. It does not claim regulatory approval, real-market coverage, or production trading use.

### Anomaly detection

An Isolation Forest model scores simulated trade features including notional, quantity, price deviation and option moneyness. The dashboard surfaces the latest anomaly score.

## Resume metrics

Use only metrics you measure yourself. The benchmark records:

- events processed/sec
- p50/p95 processing latency
- number of trades processed
- risk snapshots generated
- test count

Example resume wording after measurement:

> Built an event-driven trade-risk platform processing **X events/sec** at **Y ms p95 latency**, streaming simulated trades and market ticks through Kafka; implemented Black-Scholes Greeks, historical 95% VaR, P&L and exposure analytics with automated tests.

If anomaly detection is enabled and benchmarked:

> Added an Isolation Forest pipeline over **X+ simulated trades**, flagging **Y%** of injected anomalous transactions while exposing risk and anomaly metrics through a live Streamlit dashboard.
