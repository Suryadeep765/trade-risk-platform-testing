from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, sqrt
from scipy.stats import norm


@dataclass
class Position:
    symbol: str
    asset_type: str
    quantity: float
    avg_entry: float
    strike: float | None = None
    expiry_years: float | None = None
    option_type: str | None = None
    volatility: float = 0.25


def black_scholes(spot: float, strike: float, time: float, rate: float, vol: float, option_type: str):
    if time <= 0:
        intrinsic = max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0)
        delta = 1.0 if spot > strike else 0.0
        if option_type == "put":
            delta -= 1.0
        return intrinsic, delta, 0.0, 0.0, 0.0
    if spot <= 0 or strike <= 0 or vol <= 0:
        raise ValueError("spot, strike and volatility must be positive")
    d1 = (log(spot / strike) + (rate + 0.5 * vol**2) * time) / (vol * sqrt(time))
    d2 = d1 - vol * sqrt(time)
    disc = exp(-rate * time)
    if option_type == "call":
        price = spot * norm.cdf(d1) - strike * disc * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = -(spot * norm.pdf(d1) * vol / (2 * sqrt(time))) - rate * strike * disc * norm.cdf(d2)
    elif option_type == "put":
        price = strike * disc * norm.cdf(-d2) - spot * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        theta = -(spot * norm.pdf(d1) * vol / (2 * sqrt(time))) + rate * strike * disc * norm.cdf(-d2)
    else:
        raise ValueError("option_type must be call or put")
    gamma = norm.pdf(d1) / (spot * vol * sqrt(time))
    vega = spot * norm.pdf(d1) * sqrt(time)
    return price, delta, gamma, vega, theta


def historical_var(pnl_samples, confidence=0.95):
    import numpy as np
    samples = np.asarray(pnl_samples, dtype=float)
    if samples.size < 20:
        return 0.0
    return float(max(0.0, -np.quantile(samples, 1 - confidence)))
