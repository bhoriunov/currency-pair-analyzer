"""Functions for loading exchange rate data from the Twelve Data API."""

from datetime import datetime, timedelta

import requests

from config import API_KEY


def parse_range_to_timedelta(range_value: str) -> timedelta:
    """Convert a textual time range such as '1h' or '7d' to timedelta."""
    if range_value.endswith("h"):
        hours = int(range_value[:-1])
        return timedelta(hours=hours)

    if range_value.endswith("d"):
        days = int(range_value[:-1])
        return timedelta(days=days)

    raise ValueError("Unsupported range value.")


def _request_time_series(
    symbol: str,
    interval: str,
    start: datetime,
    end: datetime,
) -> dict:
    """Request raw OHLC data for one symbol from Twelve Data."""
    api = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end.strftime("%Y-%m-%d %H:%M:%S"),
        "apikey": API_KEY,
        "format": "JSON",
        "timezone": "UTC",
    }

    response = requests.get(api, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def _parse_values(values: list[dict]) -> list[dict]:
    """Convert raw API OHLC records to internal Python representation."""
    values = list(reversed(values))

    records = []
    for item in values:
        records.append(
            {
                "datetime": datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S"),
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
            }
        )
    return records


def _invert_records(records: list[dict]) -> list[dict]:
    """Invert OHLC records from TARGET/BASE to BASE/TARGET."""
    inverted = []

    for record in records:
        inverted.append(
            {
                "datetime": record["datetime"],
                "open": 1 / record["open"],
                "high": 1 / record["low"],
                "low": 1 / record["high"],
                "close": 1 / record["close"],
            }
        )

    return inverted


def fetch_exchange_rates(
    base: str,
    target: str,
    interval: str,
    range_value: str,
) -> list[dict]:
    """Fetch OHLC exchange rate records for the selected currency pair."""
    if base == target:
        raise ValueError("Base and target currencies must be different.")

    if not API_KEY:
        raise ValueError("Missing Twelve Data API key in config.py.")

    end = datetime.utcnow()
    start = end - parse_range_to_timedelta(range_value)

    direct_symbol = f"{base}/{target}"
    inverse_symbol = f"{target}/{base}"

    data = _request_time_series(direct_symbol, interval, start, end)

    if data.get("status") != "error":
        values = data.get("values")
        if not values:
            raise ValueError("No exchange rate data returned from API.")
        return _parse_values(values)

    message = data.get("message", "Unknown API error.")

    if "symbol" not in message.lower() and "figi" not in message.lower():
        raise ValueError(f"Twelve Data API error: {message}")

    inverse_data = _request_time_series(inverse_symbol, interval, start, end)

    if inverse_data.get("status") == "error":
        inverse_message = inverse_data.get("message", "Unknown API error.")
        raise ValueError(
            f"Twelve Data API error: {message} "
            f"Inverse pair {inverse_symbol} also failed: {inverse_message}"
        )

    inverse_values = inverse_data.get("values")
    if not inverse_values:
        raise ValueError("No exchange rate data returned from API.")

    inverse_records = _parse_values(inverse_values)
    return _invert_records(inverse_records)