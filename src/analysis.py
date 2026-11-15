"""Functions for statistical analysis of exchange rate closing prices."""

import numpy as np


def analyze_rates(closes: list[float]) -> dict:
    """Compute basic statistics and risk information from closing prices."""
    if not closes:
        raise ValueError("Rates list cannot be empty.")

    rates_array = np.array(closes, dtype=float)

    average_rate = float(np.mean(rates_array))
    min_rate = float(np.min(rates_array))
    max_rate = float(np.max(rates_array))
    last_rate = float(rates_array[-1])

    if len(rates_array) < 2:
        volatility = 0.0
        total_change = 0.0
        percent_change = 0.0
    else:
        changes = np.diff(rates_array)
        volatility = float(np.std(changes))
        total_change = float(rates_array[-1] - rates_array[0])
        percent_change = (
            0.0 if rates_array[0] == 0 else float((total_change / rates_array[0]) * 100)
        )

    if volatility < 0.002:
        risk_level = "low"
    elif volatility < 0.01:
        risk_level = "medium"
    else:
        risk_level = "high"

    summary = (
        f"The pair shows {risk_level} volatility over the selected period. "
        f"The total change was {total_change:+.4f} ({percent_change:+.2f}%)."
    )

    return {
        "average": average_rate,
        "minimum": min_rate,
        "maximum": max_rate,
        "last_rate": last_rate,
        "total_change": total_change,
        "percent_change": percent_change,
        "volatility": volatility,
        "risk_level": risk_level,
        "summary": summary,
    }
