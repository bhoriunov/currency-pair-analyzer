"""Tests for analysis functions."""
import pytest

from analysis import analyze_rates


def test_analyze_rates_basic_stats() -> None:
    """Test basic statistics for a simple input sequence."""
    result = analyze_rates([1.0, 2.0, 3.0])

    assert result["average"] == 2.0
    assert result["minimum"] == 1.0
    assert result["maximum"] == 3.0
    assert result["last_rate"] == 3.0
    assert result["total_change"] == 2.0
    assert result["percent_change"] == 200.0


def test_analyze_rates_empty_list() -> None:
    """Test that an empty input raises ValueError."""
    with pytest.raises(ValueError):
        analyze_rates([])


def test_analyze_rates_single_value() -> None:
    """Test statistics for a single-value input."""
    result = analyze_rates([5.0])

    assert result["average"] == 5.0
    assert result["minimum"] == 5.0
    assert result["maximum"] == 5.0
    assert result["last_rate"] == 5.0
    assert result["total_change"] == 0.0
    assert result["percent_change"] == 0.0
    assert result["volatility"] == 0.0


def test_analyze_rates_low_risk() -> None:
    """Test low-risk classification."""
    result = analyze_rates([1.0000, 1.0005, 1.0010, 1.0014])
    assert result["risk_level"] == "low"


def test_analyze_rates_medium_risk() -> None:
    """Test medium-risk classification."""
    result = analyze_rates([1.0, 1.005, 0.999, 1.008])
    assert result["risk_level"] == "medium"


def test_analyze_rates_high_risk() -> None:
    """Test high-risk classification."""
    result = analyze_rates([1.0, 1.03, 0.98, 1.05])
    assert result["risk_level"] == "high"
