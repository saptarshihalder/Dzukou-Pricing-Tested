"""
Configuration constants for the Dzukou pricing optimiser.

These values may be overridden on the CLI; they are defined here to
provide sensible defaults for library users.  They include sensible
defaults for concurrency, pricing margin floors and scraping settings.
"""

from __future__ import annotations

from typing import List

# Default margin floor (10 %)
DEFAULT_MARGIN_FLOOR: float = 0.10

# Default concurrency for the async scraper.  This value controls how many
# simultaneous HTTP requests will be made across all stores.  Per‑domain
# throttling is still enforced by each scraper.
DEFAULT_CONCURRENCY: int = 20

# Psychologically appealing price endings.  Prices will be rounded to
# values ending with one of these suffixes when possible.
PSYCHOLOGICAL_ENDINGS: List[float] = [0.99, 0.95]

# Default markets targeted by the optimiser.  Each string should be a
# three‑letter ISO currency code (USD, EUR, GBP, etc.).
DEFAULT_MARKETS: List[str] = ["USD", "EUR"]

# Default currency used in the internal representation.  All competitor
# prices are converted to this currency before modelling and optimisation.
BASE_CURRENCY: str = "USD"

__all__ = [
    "DEFAULT_MARGIN_FLOOR",
    "DEFAULT_CONCURRENCY",
    "PSYCHOLOGICAL_ENDINGS",
    "DEFAULT_MARKETS",
    "BASE_CURRENCY",
]
