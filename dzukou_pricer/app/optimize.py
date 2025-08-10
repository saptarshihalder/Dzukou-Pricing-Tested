"""
Price optimisation algorithms.

This module computes the optimal selling price for an item given
estimated demand elasticity and competitor information.  It performs a
grid search over a price range, subject to margin and competitive
constraints, and applies psychological price endings.
"""
from __future__ import annotations

import math
from typing import List, Tuple

from .config import DEFAULT_MARGIN_FLOOR, PSYCHOLOGICAL_ENDINGS
from .demand import expected_units


def round_to_ending(price: float, endings: List[float] = PSYCHOLOGICAL_ENDINGS) -> float:
    """Round the price down to the nearest psychological ending.

    For example, with endings [0.99, 0.95], 12.37 becomes 11.99 and
    15.02 becomes 14.95.
    """
    integer_part = int(math.floor(price))
    for ending in sorted(endings, reverse=True):
        candidate = integer_part + ending
        if candidate <= price:
            return round(candidate, 2)
    return round(price, 2)


def optimise_price(
    cogs: float,
    elasticity: float,
    current_price: float | None,
    competitor_min_price: float | None,
    margin_floor: float = DEFAULT_MARGIN_FLOOR,
    baseline_units: float = 100.0,
    price_step: float = 0.50,
) -> Tuple[float, float, float, float, float]:
    """Compute the optimal price via a simple grid search.

    The objective is to maximise profit = (price - cogs) * units(price).

    :param cogs: Cost of goods sold.
    :param elasticity: Demand elasticity (negative).
    :param current_price: Current price; used for baseline units and guardrails.
    :param competitor_min_price: Minimum competitor price; used for guardrails.
    :param margin_floor: Minimum margin above COGS (fraction).
    :param baseline_units: Estimated units sold at the current price.
    :param price_step: Granularity of the price search grid.
    :returns: Tuple of (recommended_price, expected_units, expected_profit,
              profit_uplift_vs_current_pct, demand_lift_vs_current_pct).
    """
    if cogs <= 0:
        raise ValueError("COGS must be positive to compute margin floor")
    # Determine reference price and baseline units
    reference_price = current_price if current_price and current_price > 0 else cogs * (1 + margin_floor)
    baseline_units = baseline_units
    # Determine price bounds
    lower_bound = max(cogs * (1 + margin_floor), (competitor_min_price or reference_price) * 0.8)
    # Upper bound not more than 20 % above min competitor unless unknown
    if competitor_min_price:
        upper_bound = competitor_min_price * 1.2
    else:
        upper_bound = reference_price * 1.5
    # Guarantee upper bound >= lower bound + small epsilon
    if upper_bound < lower_bound:
        upper_bound = lower_bound * 1.2
    # Search grid
    best_price = lower_bound
    best_units = 0.0
    best_profit = -float("inf")
    prices_to_check: List[float] = []
    p = lower_bound
    while p <= upper_bound + 1e-6:
        prices_to_check.append(round_to_ending(p))
        p += price_step
    # Deduplicate prices
    prices_to_check = sorted(set(prices_to_check))
    for price in prices_to_check:
        units = expected_units(baseline_units, price, reference_price, elasticity)
        profit = (price - cogs) * units
        if profit > best_profit:
            best_profit = profit
            best_price = price
            best_units = units
    # Compute uplift metrics
    # Profit and demand uplift vs current price
    if current_price and current_price > 0:
        current_units = expected_units(baseline_units, current_price, reference_price, elasticity)
        current_profit = (current_price - cogs) * current_units
        profit_uplift_pct = ((best_profit - current_profit) / current_profit) * 100.0 if current_profit != 0 else None
        demand_uplift_pct = ((best_units - current_units) / current_units) * 100.0 if current_units != 0 else None
    else:
        profit_uplift_pct = None
        demand_uplift_pct = None
    return best_price, best_units, best_profit, profit_uplift_pct, demand_uplift_pct


__all__ = ["optimise_price"]
