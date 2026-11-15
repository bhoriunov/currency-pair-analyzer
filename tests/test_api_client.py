"""Tests for API client helper functions."""
from datetime import timedelta

import pytest

from api_client import parse_range_to_timedelta


def test_parse_range_hours() -> None:
    """Test hour-based range parsing."""
    assert parse_range_to_timedelta("1h") == timedelta(hours=1)
    assert parse_range_to_timedelta("6h") == timedelta(hours=6)


def test_parse_range_days() -> None:
    """Test day-based range parsing."""
    assert parse_range_to_timedelta("7d") == timedelta(days=7)
    assert parse_range_to_timedelta("30d") == timedelta(days=30)


def test_parse_range_invalid() -> None:
    """Test that an invalid range raises ValueError."""
    with pytest.raises(ValueError):
        parse_range_to_timedelta("10x")
