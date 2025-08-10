"""
Feature engineering for pricing optimisation.

This module derives explanatory features from matched competitor
listings, which are later fed into the demand model and optimiser.
"""
from __future__ import annotations

from statistics import median
from typing import List

from .types import MatchedCandidate


def compute_competitor_features(
    current_price: float | None,
    candidates: List[MatchedCandidate],
) -> dict:
    """Compute summary statistics of competitor prices.

    :param current_price: The current selling price of our item.
    :param candidates: List of matched competitor listings with effective prices.
    :returns: A dictionary of features.
    """
    prices = [cand.effective_price for cand in candidates if cand.effective_price]
    # If no prices, return default values
    if not prices:
        return {
            "min_competitor": None,
            "median_competitor": None,
            "max_competitor": None,
            "spread": None,
            "num_competitors": 0,
            "competitor_index": None,
            "undercut_pct": None,
        }
    min_price = min(prices)
    max_price = max(prices)
    med_price = median(prices)
    spread = max_price - min_price
    num = len(prices)
    competitor_index = None
    undercut_pct = None
    if current_price and current_price > 0:
        competitor_index = min_price / current_price
        undercut_pct = (current_price - min_price) / current_price
    return {
        "min_competitor": min_price,
        "median_competitor": med_price,
        "max_competitor": max_price,
        "spread": spread,
        "num_competitors": num,
        "competitor_index": competitor_index,
        "undercut_pct": undercut_pct,
    }


def price_ending_feature(price: float) -> float:
    """Return the decimal part of a price to capture price endings."""
    return price - int(price)


__all__ = [
    "compute_competitor_features",
    "price_ending_feature",
]
