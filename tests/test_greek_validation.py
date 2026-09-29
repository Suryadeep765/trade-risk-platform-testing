import numpy as np

from src.models.risk import black_scholes


def finite_difference_validation(
    spot,
    strike,
    time,
    rate,
    volatility,
    option_type,
):
    h_spot = max(1e-3, spot * 1e-4)
    h_vol = 1e-4

    base = black_scholes(
        spot,
        strike,
        time,
        rate,
        volatility,
        option_type,
    )

    up = black_scholes(
        spot + h_spot,
        strike,
        time,
        rate,
        volatility,
        option_type,
    )

    down = black_scholes(
        spot - h_spot,
        strike,
        time,
        rate,
        volatility,
        option_type,
    )

    vol_up = black_scholes(
        spot,
        strike,
        time,
        rate,
        volatility + h_vol,
        option_type,
    )

    vol_down = black_scholes(
        spot,
        strike,
        time,
        rate,
        volatility - h_vol,
        option_type,
    )

    numerical_delta = (
        up[0] - down[0]
    ) / (2 * h_spot)

    numerical_gamma = (
        up[0]
        - 2 * base[0]
        + down[0]
    ) / (h_spot ** 2)

    numerical_vega = (
        vol_up[0]
        - vol_down[0]
    ) / (2 * h_vol)

    return {
        "analytical_delta": base[1],
        "numerical_delta": numerical_delta,
        "analytical_gamma": base[2],
        "numerical_gamma": numerical_gamma,
        "analytical_vega": base[3],
        "numerical_vega": numerical_vega,
    }


def relative_error(actual, expected):
    scale = max(abs(expected), 1e-6)

    return abs(actual - expected) / scale


def test_randomized_greek_validation():

    rng = np.random.default_rng(42)

    errors_delta = []
    errors_gamma = []
    errors_vega = []

    absolute_gamma_errors = []
    absolute_vega_errors = []

    for _ in range(1000):

        spot = float(
            rng.uniform(50, 500)
        )

        strike = float(
            rng.uniform(50, 500)
        )

        time = float(
            rng.uniform(0.1, 3.0)
        )

        rate = float(
            rng.uniform(0.0, 0.10)
        )

        volatility = float(
            rng.uniform(0.10, 0.60)
        )

        option_type = str(
            rng.choice(["call", "put"])
        )

        result = finite_difference_validation(
            spot,
            strike,
            time,
            rate,
            volatility,
            option_type,
        )

        errors_delta.append(
            relative_error(
                result["analytical_delta"],
                result["numerical_delta"],
            )
        )

        errors_gamma.append(
            relative_error(
                result["analytical_gamma"],
                result["numerical_gamma"],
            )
        )

        errors_vega.append(
            relative_error(
                result["analytical_vega"],
                result["numerical_vega"],
            )
        )

        absolute_gamma_errors.append(
            abs(
                result["analytical_gamma"]
                - result["numerical_gamma"]
            )
        )

        absolute_vega_errors.append(
            abs(
                result["analytical_vega"]
                - result["numerical_vega"]
            )
        )

    max_delta_error = max(errors_delta)
    median_delta_error = float(
        np.median(errors_delta)
    )

    max_gamma_error = max(errors_gamma)
    median_gamma_error = float(
        np.median(errors_gamma)
    )

    max_vega_error = max(errors_vega)
    median_vega_error = float(
        np.median(errors_vega)
    )

    max_gamma_absolute_error = max(
        absolute_gamma_errors
    )

    max_vega_absolute_error = max(
        absolute_vega_errors
    )

    print()
    print("=" * 70)
    print("RANDOMIZED GREEK VALIDATION")
    print("=" * 70)

    print(
        "Scenarios tested:          1,000"
    )

    print()

    print(
        f"Delta max relative error:  "
        f"{max_delta_error:.8%}"
    )

    print(
        f"Delta median error:        "
        f"{median_delta_error:.8%}"
    )

    print()

    print(
        f"Gamma max relative error:  "
        f"{max_gamma_error:.8%}"
    )

    print(
        f"Gamma median error:        "
        f"{median_gamma_error:.8%}"
    )

    print(
        f"Gamma max absolute error:  "
        f"{max_gamma_absolute_error:.10e}"
    )

    print()

    print(
        f"Vega max relative error:   "
        f"{max_vega_error:.8%}"
    )

    print(
        f"Vega median error:         "
        f"{median_vega_error:.8%}"
    )

    print(
        f"Vega max absolute error:   "
        f"{max_vega_absolute_error:.10e}"
    )

    print("=" * 70)

    assert max_delta_error < 1e-4

    assert max_gamma_absolute_error < 1e-5

    assert max_vega_absolute_error < 1e-3