import pytest

from src.models.risk import black_scholes


def test_standard_black_scholes_call():

    price, delta, gamma, vega, theta = black_scholes(
        spot=100.0,
        strike=100.0,
        time=1.0,
        rate=0.05,
        vol=0.20,
        option_type="call",
    )

    assert price == pytest.approx(
        10.45058357,
        rel=1e-6,
    )

    assert delta == pytest.approx(
        0.63683065,
        rel=1e-6,
    )

    assert gamma == pytest.approx(
        0.01876202,
        rel=1e-6,
    )

    assert vega == pytest.approx(
        37.52403469,
        rel=1e-6,
    )

    assert theta == pytest.approx(
        -6.41402755,
        rel=1e-6,
    )


def test_standard_black_scholes_put():

    price, delta, gamma, vega, theta = black_scholes(
        spot=100.0,
        strike=100.0,
        time=1.0,
        rate=0.05,
        vol=0.20,
        option_type="put",
    )

    assert price == pytest.approx(
        5.57352602,
        rel=1e-6,
    )

    assert delta == pytest.approx(
        -0.36316935,
        rel=1e-6,
    )

    assert gamma == pytest.approx(
        0.01876202,
        rel=1e-6,
    )

    assert vega == pytest.approx(
        37.52403469,
        rel=1e-6,
    )

    assert theta == pytest.approx(
        -1.65788042,
        rel=1e-6,
    )