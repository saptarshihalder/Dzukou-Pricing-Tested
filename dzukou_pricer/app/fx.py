"""
Currency conversion utilities.

This module wraps the `currencyconverter` library and provides a simple
fallback conversion table when live rates are unavailable.  All prices
within the optimiser are converted to the base currency prior to
modelling.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

try:
    from currencyconverter import CurrencyConverter  # type: ignore
except ImportError:  # pragma: no cover
    CurrencyConverter = None

from .config import BASE_CURRENCY

# Fallback rates relative to USD (approximate).  These rates are
# intentionally conservative and should be updated periodically.
FALLBACK_RATES = {
    ("EUR", "USD"): 1.10,
    ("GBP", "USD"): 1.25,
    ("USD", "EUR"): 0.91,
    ("GBP", "EUR"): 1.14,
    ("EUR", "GBP"): 0.88,
    ("USD", "GBP"): 0.80,
}


@lru_cache(maxsize=16)
def get_converter() -> Optional[CurrencyConverter]:
    """Lazily instantiate a :class:`CurrencyConverter` if available."""
    if CurrencyConverter is None:
        return None
    try:
        return CurrencyConverter()
    except Exception:  # pragma: no cover
        return None


def convert(
    amount: float,
    from_currency: str,
    to_currency: str = BASE_CURRENCY,
) -> float:
    """Convert a monetary amount from one currency to another.

    If a live converter is available and contains the requested
    currencies, it will be used.  Otherwise, a static fallback rate
    will be applied.  If the currencies are identical, the amount is
    returned unchanged.
    """
    from_cur = from_currency.upper()
    to_cur = to_currency.upper()
    if from_cur == to_cur:
        return amount
    converter = get_converter()
    if converter is not None:
        try:
            return converter.convert(amount, from_cur, to_cur)
        except Exception:
            pass
    # Use fallback
    rate = FALLBACK_RATES.get((from_cur, to_cur))
    if rate is None:
        # If missing direct pair, invert or default to identity
        inverse = FALLBACK_RATES.get((to_cur, from_cur))
        if inverse is not None:
            rate = 1.0 / inverse
        else:
            rate = 1.0  # no conversion available
    return amount * rate


__all__ = ["convert"]
