from __future__ import annotations

import time
from collections import defaultdict, deque

import numpy as np
from sklearn.ensemble import IsolationForest

from src.models.risk import black_scholes, historical_var


SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA"]


def generate_data(n_trades=10000, n_market=90000, seed=42):
    rng = np.random.default_rng(seed)

    trades = []

    spot_prices = {
        symbol: float(rng.uniform(100, 500))
        for symbol in SYMBOLS
    }

    for _ in range(n_trades):
        symbol = str(rng.choice(SYMBOLS))

        asset_type = str(
            rng.choice(
                ["EQUITY", "OPTION"],
                p=[0.7, 0.3],
            )
        )

        quantity = int(rng.integers(1, 101))
        quantity *= int(rng.choice([-1, 1]))

        spot = spot_prices[symbol]

        if asset_type == "EQUITY":

            entry_price = float(
                spot * rng.uniform(0.98, 1.02)
            )

            trades.append(
                {
                    "symbol": symbol,
                    "asset_type": "EQUITY",
                    "quantity": quantity,
                    "price": entry_price,
                }
            )

        else:

            strike = float(
                spot * rng.uniform(0.85, 1.15)
            )

            expiry = float(
                rng.uniform(0.25, 2.0)
            )

            volatility = float(
                rng.uniform(0.15, 0.40)
            )

            rate = 0.05

            option_type = str(
                rng.choice(["call", "put"])
            )

            option_price, _, _, _, _ = black_scholes(
                spot,
                strike,
                expiry,
                rate,
                volatility,
                option_type,
            )

            entry_price = float(
                option_price * rng.uniform(0.98, 1.02)
            )

            trades.append(
                {
                    "symbol": symbol,
                    "asset_type": "OPTION",
                    "quantity": quantity,
                    "price": entry_price,
                    "strike": strike,
                    "expiry_years": expiry,
                    "option_type": option_type,
                    "volatility": volatility,
                    "rate": rate,
                }
            )

    market_events = []

    for _ in range(n_market):

        symbol = str(rng.choice(SYMBOLS))

        spot_prices[symbol] *= (
            1 + rng.normal(0, 0.001)
        )

        market_events.append(
            {
                "symbol": symbol,
                "price": spot_prices[symbol],
            }
        )

    return trades, market_events


def calculate_snapshot(
    positions,
    prices,
    return_history,
):

    pnl = 0.0
    gross = 0.0
    net = 0.0

    delta = 0.0
    gamma = 0.0
    vega = 0.0
    theta = 0.0

    pnl_samples = []

    for symbol, trades in positions.items():

        spot = prices.get(symbol)

        if spot is None:
            continue

        for trade in trades:

            qty = trade["quantity"]
            entry = trade["price"]

            if trade["asset_type"] == "EQUITY":

                value = qty * spot

                trade_pnl = (
                    qty *
                    (spot - entry)
                )

                d = qty
                g = 0.0
                v = 0.0
                th = 0.0

            else:

                option_price, d, g, v, th = black_scholes(
                    spot,
                    trade["strike"],
                    trade["expiry_years"],
                    trade["rate"],
                    trade["volatility"],
                    trade["option_type"],
                )

                value = (
                    qty *
                    option_price *
                    100
                )

                trade_pnl = (
                    qty *
                    (option_price - entry) *
                    100
                )

                d *= qty * 100
                g *= qty * 100
                v *= qty * 100
                th *= qty * 100

            pnl += trade_pnl

            gross += abs(value)

            net += value

            delta += d
            gamma += g
            vega += v
            theta += th

            pnl_samples.append(
                trade_pnl
            )

    simulated_pnl = []

    for symbol, returns in return_history.items():

        equity_exposure = sum(
            trade["quantity"] *
            trade["price"]
            for trade in positions.get(
                symbol,
                []
            )
            if trade["asset_type"] == "EQUITY"
        )

        simulated_pnl.extend(
            equity_exposure * r
            for r in returns
        )

    var95 = historical_var(
        simulated_pnl
        if simulated_pnl
        else pnl_samples,
        0.95,
    )

    return {
        "pnl": pnl,
        "gross_exposure": gross,
        "net_exposure": net,
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "var95": var95,
    }


def run_benchmark(
    n_trades=10000,
    n_market=90000,
    snapshot_interval=1000,
):

    print(
        f"Generating {n_trades + n_market:,} events..."
    )

    trades, market_events = generate_data(
        n_trades=n_trades,
        n_market=n_market,
    )

    positions = defaultdict(list)

    prices = {}

    return_history = defaultdict(
        lambda: deque(maxlen=500)
    )

    anomaly_features = []

    event_latencies = []

    snapshot_latencies = []

    trade_index = 0
    market_index = 0

    snapshots = 0

    total_events = (
        n_trades +
        n_market
    )

    start = time.perf_counter()

    for event_index in range(total_events):

        event_start = time.perf_counter()

        if trade_index < n_trades:

            trade = trades[trade_index]

            trade_index += 1

            positions[
                trade["symbol"]
            ].append(trade)

            feature = [
                abs(
                    trade["quantity"] *
                    trade["price"]
                ),
                abs(
                    trade["quantity"]
                ),
                trade["price"],
                abs(
                    trade.get(
                        "strike",
                        trade["price"],
                    )
                    - trade["price"]
                )
                / max(
                    trade["price"],
                    1,
                ),
            ]

            anomaly_features.append(
                feature
            )

        else:

            event = market_events[
                market_index
            ]

            market_index += 1

            symbol = event["symbol"]

            previous = prices.get(
                symbol
            )

            prices[symbol] = (
                event["price"]
            )

            if previous is not None:

                return_history[
                    symbol
                ].append(
                    event["price"]
                    / previous
                    - 1
                )

        event_latencies.append(
            (
                time.perf_counter()
                - event_start
            )
            * 1000
        )

        if (
            event_index %
            snapshot_interval
            == 0
        ):

            snapshot_start = (
                time.perf_counter()
            )

            calculate_snapshot(
                positions,
                prices,
                return_history,
            )

            snapshot_latencies.append(
                (
                    time.perf_counter()
                    - snapshot_start
                )
                * 1000
            )

            snapshots += 1

    total_time = (
        time.perf_counter()
        - start
    )

    anomaly_count = 0

    if len(anomaly_features) >= 50:

        model = IsolationForest(
            contamination=0.03,
            random_state=42,
        )

        labels = model.fit_predict(
            np.asarray(
                anomaly_features[-500:]
            )
        )

        anomaly_count = int(
            (labels == -1).sum()
        )

    final_snapshot = calculate_snapshot(
        positions,
        prices,
        return_history,
    )

    event_latencies = np.asarray(
        event_latencies
    )

    snapshot_latencies = np.asarray(
        snapshot_latencies
    )

    print()
    print("=" * 65)
    print(
        "LOCAL TRADE RISK PLATFORM BENCHMARK"
    )
    print("=" * 65)

    print(
        f"Trades processed:       "
        f"{n_trades:,}"
    )

    print(
        f"Market events:          "
        f"{n_market:,}"
    )

    print(
        f"Total events:           "
        f"{total_events:,}"
    )

    print(
        f"Risk snapshots:         "
        f"{snapshots:,}"
    )

    print()

    print(
        f"Total runtime:          "
        f"{total_time:.4f} sec"
    )

    print(
        f"Event throughput:       "
        f"{total_events / total_time:,.2f} events/sec"
    )

    print()

    print(
        f"Event latency p50:      "
        f"{np.percentile(event_latencies, 50):.4f} ms"
    )

    print(
        f"Event latency p95:      "
        f"{np.percentile(event_latencies, 95):.4f} ms"
    )

    print(
        f"Event latency p99:      "
        f"{np.percentile(event_latencies, 99):.4f} ms"
    )

    print()

    print(
        f"Risk snapshot p50:      "
        f"{np.percentile(snapshot_latencies, 50):.4f} ms"
    )

    print(
        f"Risk snapshot p95:      "
        f"{np.percentile(snapshot_latencies, 95):.4f} ms"
    )

    print(
        f"Risk snapshot p99:      "
        f"{np.percentile(snapshot_latencies, 99):.4f} ms"
    )

    print()

    print(
        f"Final P&L:              "
        f"{final_snapshot['pnl']:,.2f}"
    )

    print(
        f"Gross exposure:         "
        f"{final_snapshot['gross_exposure']:,.2f}"
    )

    print(
        f"Net exposure:           "
        f"{final_snapshot['net_exposure']:,.2f}"
    )

    print(
        f"Delta:                  "
        f"{final_snapshot['delta']:,.2f}"
    )

    print(
        f"Gamma:                  "
        f"{final_snapshot['gamma']:,.6f}"
    )

    print(
        f"Vega:                   "
        f"{final_snapshot['vega']:,.2f}"
    )

    print(
        f"Theta:                  "
        f"{final_snapshot['theta']:,.2f}"
    )

    print(
        f"95% Historical VaR:     "
        f"{final_snapshot['var95']:,.2f}"
    )

    print(
        f"Anomalies detected:     "
        f"{anomaly_count:,}"
    )

    print("=" * 65)


if __name__ == "__main__":
    run_benchmark()