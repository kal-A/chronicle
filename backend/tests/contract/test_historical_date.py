"""Era-capable HistoricalDate (ADR-005).

The canonical ordering key is a signed astronomical year (1 = 1 CE, 0 = 1 BC,
-1 = 2 BC, …); the calendar dates are optional CE-only day/month precision.
These tests prove BC works, CE stays backward compatible, ordering is total
across the boundary, and the honesty invariants hold. Mirrors the frontend
schema.test.ts additions for HistoricalDateSchema.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from chronicle.contracts.enums import DatePrecision
from chronicle.contracts.shared import HistoricalDate


def test_ce_date_only_stays_valid_and_derives_its_year():
    """Existing CE records carry no year field; the key is derived from the date."""
    hd = HistoricalDate(precision=DatePrecision.EXACT, earliest=date(1914, 7, 5), latest=date(1914, 7, 5))
    assert hd.lower_key == (1914, 186)
    assert hd.upper_key == (1914, 186)


def test_bc_year_only_is_representable_without_a_calendar_date():
    hd = HistoricalDate(
        precision=DatePrecision.RANGE,
        earliestYear=-218,  # 219 BC
        latestYear=-201,  # 202 BC
        label="218–201 BC",
    )
    assert hd.earliest is None and hd.latest is None
    assert hd.lower_key == (-218, 1)
    assert hd.upper_key == (-201, 366)


def test_ordering_is_total_across_the_bc_ce_boundary():
    bc = HistoricalDate(precision=DatePrecision.RANGE, earliestYear=-44, latestYear=-44)
    ce = HistoricalDate(precision=DatePrecision.EXACT, earliest=date(9, 1, 1), latest=date(9, 1, 1))
    assert bc.upper_key < ce.lower_key  # 45 BC precedes 9 CE


def test_a_bound_must_be_derivable_from_a_year_or_a_date():
    with pytest.raises(ValidationError, match="earliest or earliestYear"):
        HistoricalDate(precision=DatePrecision.RANGE, latestYear=100)
    with pytest.raises(ValidationError, match="latest or latestYear"):
        HistoricalDate(precision=DatePrecision.RANGE, earliestYear=100)


def test_year_field_and_calendar_date_must_agree():
    with pytest.raises(ValidationError, match="earliest.year must equal earliestYear"):
        HistoricalDate(
            precision=DatePrecision.RANGE,
            earliest=date(1914, 1, 1),
            earliestYear=1913,
            latest=date(1914, 12, 31),
        )


def test_earliest_after_latest_rejected_across_eras():
    with pytest.raises(ValidationError, match="earliest must not be after latest"):
        HistoricalDate(precision=DatePrecision.RANGE, earliestYear=-100, latestYear=-200)


def test_exact_requires_equal_bounds_for_bc_too():
    with pytest.raises(ValidationError, match="exact"):
        HistoricalDate(precision=DatePrecision.EXACT, earliestYear=-44, latestYear=-43)
    # equal signed years are a valid exact BC date
    HistoricalDate(precision=DatePrecision.EXACT, earliestYear=-44, latestYear=-44)
