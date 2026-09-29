import numpy as np

from src.models.risk import black_scholes, historical_var


def test_call_price_positive():
    price, delta, gamma, vega, theta = black_scholes(100, 100, 1, 0.05, 0.2, "call")
    assert 10 < price < 12
    assert 0 < delta < 1
    assert gamma > 0
    assert vega > 0
    assert theta < 0


def test_put_call_delta_relationship():
    _, call_delta, *_ = black_scholes(100, 100, 1, 0.05, 0.2, "call")
    _, put_delta, *_ = black_scholes(100, 100, 1, 0.05, 0.2, "put")
    assert abs((call_delta - put_delta) - 1) < 1e-10


def test_var_is_non_negative():
    pnl = np.array([2, 1, 0, -1, -2, -4, 3] * 20, dtype=float)
    assert historical_var(pnl, 0.95) >= 0


def test_var_requires_history():
    assert historical_var([1, -1, 2], 0.95) == 0
