# Currency Pair Analyzer

Desktop application in Python for analyzing foreign exchange rates with an interactive graphical user interface.

## Project Description

Currency Pair Analyzer is a PyQt6 desktop application that allows the user to load and analyze exchange rate data for selected currency pairs. The application displays the data in both line and candlestick charts, computes basic statistics, allows CSV export, and supports interactive chart navigation.

The project was created as a semestral assignment for BI-PYT.

## Features

- selection of base and target currency
- selection of interval and available time range
- loading real exchange rate data from Twelve Data API
- line chart visualization
- candlestick chart visualization
- computed statistics:
  - average rate
  - minimum rate
  - maximum rate
  - last rate
  - total change
  - percent change
  - volatility
  - risk level
- textual summary of the selected data
- interactive chart controls:
  - zoom with mouse wheel
  - drag to pan
  - double click to reset chart view
  - hover tooltip with current price
  - selected price display after click
- CSV export of loaded OHLC data
- handling of invalid currency selections and API errors

## Technologies Used

- Python 3
- PyQt6
- matplotlib
- mplfinance
- pandas
- numpy
- requests
- pytest

## Project Structure

```text
src/
├── main.py
├── gui.py
├── api_client.py
├── analysis.py
└── config.py

tests/
├── test_analysis.py
└── test_api_client.py
```

## Requirements

- Python 3.9+
- internet connection

## Installation

Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application
```bash
python src/main.py
```

The application uses the Twelve Data API.

A personal API key is required to fetch live market data.
Set the `TWELVE_DATA_API_KEY` environment variable
before launching the application.

## Running Tests
```bash
pytest
```

## Notes

* The application uses the Twelve Data API for downloading exchange rate data.
* Not all currency pairs may be supported by the external API.
* Some interval and range combinations may return an API error depending on provider support.
* On macOS, a LibreSSL warning may appear when running tests. This does not affect the functionality of the project.