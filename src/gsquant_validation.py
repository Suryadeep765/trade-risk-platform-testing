from __future__ import annotations

import argparse
import os

from src.models.risk import black_scholes


def our_model(
    spot,
    strike,
    time,
    rate,
    volatility,
    option_type,
):
    return black_scholes(
        spot,
        strike,
        time,
        rate,
        volatility,
        option_type,
    )


def print_local_result(
    spot,
    strike,
    time,
    rate,
    volatility,
    option_type,
):
    result = our_model(
        spot,
        strike,
        time,
        rate,
        volatility,
        option_type,
    )

    price, delta, gamma, vega, theta = result

    print()
    print("=" * 65)
    print("OUR BLACK-SCHOLES ENGINE")
    print("=" * 65)

    print(f"Spot:                   {spot:.6f}")
    print(f"Strike:                 {strike:.6f}")
    print(f"Time:                   {time:.6f} years")
    print(f"Rate:                   {rate:.6f}")
    print(f"Volatility:             {volatility:.6f}")
    print(f"Option type:            {option_type}")

    print()

    print(f"Price:                  {price:.10f}")
    print(f"Delta:                  {delta:.10f}")
    print(f"Gamma:                  {gamma:.10f}")
    print(f"Vega:                   {vega:.10f}")
    print(f"Theta:                  {theta:.10f}")

    print("=" * 65)

    return result


def gs_quant_result(
    spot,
    strike,
    time,
    option_type,
):
    try:
        from gs_quant.instrument import (
            EqOption,
            OptionStyle,
            OptionType,
        )
        from gs_quant.risk import (
            EqDelta,
            EqGamma,
            EqVega,
            Price,
        )
        from gs_quant.session import (
            Environment,
            GsSession,
        )

    except ImportError as exc:
        print()
        print("GS Quant is not installed.")
        print()
        print("Install it with:")
        print("pip install gs-quant")
        print()
        print(f"Import error: {exc}")
        return None

    client_id = os.getenv(
        "GSQUANT_CLIENT_ID"
    )

    client_secret = os.getenv(
        "GSQUANT_CLIENT_SECRET"
    )

    if not client_id or not client_secret:
        print()
        print("=" * 65)
        print("GS QUANT VALIDATION NOT RUN")
        print("=" * 65)
        print(
            "GS Quant is installed, but no API credentials "
            "were supplied."
        )
        print()
        print(
            "This is expected: GS Quant's documented "
            "pricing/risk examples use a GsSession and "
            "appropriate entitlements."
        )
        print()
        print(
            "Set these environment variables when you have "
            "GS Developer credentials:"
        )
        print()
        print(
            "$env:GSQUANT_CLIENT_ID='your-client-id'"
        )
        print(
            "$env:GSQUANT_CLIENT_SECRET='your-client-secret'"
        )
        print("=" * 65)

        return None

    try:

        GsSession.use(
            environment_or_domain=Environment.PROD,
            client_id=client_id,
            client_secret=client_secret,
            scopes=("run_analytics",),
        )

        option_type_enum = (
            OptionType.Call
            if option_type.lower() == "call"
            else OptionType.Put
        )

        option = EqOption(
            underlier="AAPL UW",
            expiration_date=f"{time}y",
            strike_price=strike,
            option_type=option_type_enum,
            option_style=OptionStyle.European,
        )

        price = option.calc(Price)
        eq_delta = option.calc(EqDelta)
        eq_gamma = option.calc(EqGamma)
        eq_vega = option.calc(EqVega)

        if hasattr(price, "result"):
            price = price.result()

        if hasattr(eq_delta, "result"):
            eq_delta = eq_delta.result()

        if hasattr(eq_gamma, "result"):
            eq_gamma = eq_gamma.result()

        if hasattr(eq_vega, "result"):
            eq_vega = eq_vega.result()

        print()
        print("=" * 65)
        print("GS QUANT")
        print("=" * 65)

        print(f"Price:                  {price}")
        print(f"EqDelta:                {eq_delta}")
        print(f"EqGamma:                {eq_gamma}")
        print(f"EqVega:                 {eq_vega}")

        print("=" * 65)

        return {
            "price": price,
            "eq_delta": eq_delta,
            "eq_gamma": eq_gamma,
            "eq_vega": eq_vega,
        }

    except Exception as exc:

        print()
        print("=" * 65)
        print("GS QUANT REQUEST FAILED")
        print("=" * 65)
        print(type(exc).__name__)
        print(str(exc))
        print("=" * 65)

        return None


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate the local Black-Scholes implementation "
            "against GS Quant when credentials are available."
        )
    )

    parser.add_argument(
        "--spot",
        type=float,
        default=100.0,
    )

    parser.add_argument(
        "--strike",
        type=float,
        default=100.0,
    )

    parser.add_argument(
        "--time",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--rate",
        type=float,
        default=0.05,
    )

    parser.add_argument(
        "--volatility",
        type=float,
        default=0.20,
    )

    parser.add_argument(
        "--option-type",
        choices=["call", "put"],
        default="call",
    )

    args = parser.parse_args()

    print_local_result(
        args.spot,
        args.strike,
        args.time,
        args.rate,
        args.volatility,
        args.option_type,
    )

    gs_quant_result(
        args.spot,
        args.strike,
        args.time,
        args.option_type,
    )


if __name__ == "__main__":
    main()