"""
Demand modelling for pricing optimisation.

This module provides functions to estimate expected demand as a function of
price.  It uses simple category‑level priors when no historical
sales data are available.  If sales history is provided, more
sophisticated models could be plugged in here.
"""
from __future__ import annotations

from typing import Optional

from .types import Item

# Category priors for price elasticity.  These values should be
# calibrated using historical sales data or industry studies.
CATEGORY_ELASTICITY_PRIORS: dict[str, float] = {
    "default": -1.2,
    "clothing": -1.5,
    "home": -1.1,
    "accessories": -1.3,
    # Add more categories as needed
}


def get_elasticity(item: Item) -> float:
    """Retrieve a price elasticity for the given item.

    :returns: Elasticity value (negative for normal goods).
    """
    if item.category and item.category.lower() in CATEGORY_ELASTICITY_PRIORS:
        return CATEGORY_ELASTICITY_PRIORS[item.category.lower()]
    return CATEGORY_ELASTICITY_PRIORS["default"]


def expected_units(
    baseline_units: float,
    price: float,
    reference_price: float,
    elasticity: float,
) -> float:
    """Compute expected units sold at a given price using a power law.

    :param baseline_units: Estimated units sold at the reference price.
    :param price: Price at which to estimate demand.
    :param reference_price: Reference price corresponding to baseline units.
    :param elasticity: Price elasticity (negative).
    :returns: Expected units at the proposed price.
    """
    if price <= 0 or reference_price <= 0:
        return 0.0
    # Demand follows (P / P_ref) ** elasticity
    ratio = price / reference_price
    return baseline_units * (ratio ** elasticity)


__all__ = ["get_elasticity", "expected_units"]
