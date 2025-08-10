"""
Type definitions used throughout the Dzukou pricing optimiser.

We use Pydantic models for ease of serialisation and validation.  These
types describe catalogue items, competitor listings, matched candidates
and optimisation results.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Item(BaseModel):
    """Represents a product in the user's catalogue."""

    item_id: str = Field(..., description="Unique identifier for the item")
    item_name: str = Field(..., description="Human‑readable name of the item")
    brand: Optional[str] = Field(None, description="Brand name, if known")
    category: Optional[str] = Field(None, description="Product category")
    cogs: Optional[float] = Field(None, description="Cost of goods sold")
    current_price: Optional[float] = Field(None, description="Current selling price")
    currency: Optional[str] = Field(None, description="Currency of the current price")
    size: Optional[str] = Field(None, description="Size/weight/volume information")
    pack_count: Optional[int] = Field(None, description="Number of units per pack")
    # Additional attributes can be included as needed


class Candidate(BaseModel):
    """Represents a competitor listing for a product."""

    store: str = Field(..., description="Name of the competitor store")
    url: str = Field(..., description="URL of the competitor listing")
    title: str = Field(..., description="Title of the competitor listing")
    brand: Optional[str] = Field(None, description="Brand extracted from the listing")
    size: Optional[str] = Field(None, description="Size/pack information from listing")
    shelf_price: Optional[float] = Field(None, description="Shelf price as displayed")
    compare_at_price: Optional[float] = Field(None, description="Compare‑at/list price")
    shipping_cost: Optional[float] = Field(None, description="Shipping cost if any")
    vat_included: Optional[bool] = Field(None, description="True if VAT is included")
    currency: Optional[str] = Field(None, description="Currency of the price")
    stock: Optional[str] = Field(None, description="Stock status (in_stock, oos, etc.)")
    rating_count: Optional[int] = Field(None, description="Number of ratings/reviews")


class MatchedCandidate(BaseModel):
    """A candidate listing matched to one of our catalogue items."""

    candidate: Candidate = Field(..., description="The competitor listing")
    match_score: float = Field(..., description="Similarity score between 0 and 1")
    effective_price: Optional[float] = Field(
        None, description="Price used in modelling after shipping and tax adjustments"
    )


class PriceRecommendation(BaseModel):
    """Represents an optimisation result for a single item."""

    item_id: str = Field(..., description="ID of the product being optimised")
    current_price: Optional[float] = Field(None, description="Current price of the item")
    recommended_price: Optional[float] = Field(
        None, description="Optimal price as computed by the optimiser"
    )
    currency: str = Field(..., description="Currency for the recommended price")
    expected_units: Optional[float] = Field(
        None, description="Expected units sold at the recommended price"
    )
    expected_profit: Optional[float] = Field(
        None, description="Expected profit at the recommended price"
    )
    profit_uplift_vs_current_pct: Optional[float] = Field(
        None, description="Profit uplift versus current price (%)"
    )
    demand_lift_vs_current_pct: Optional[float] = Field(
        None, description="Demand uplift versus current price (%)"
    )
    competitor_summary: List[MatchedCandidate] = Field(
        default_factory=list, description="Competitor listings considered"
    )
    rationale: Optional[str] = Field(None, description="Human‑readable explanation")
    confidence: Optional[str] = Field(None, description="Confidence level")
    flags: List[str] = Field(default_factory=list, description="Warnings/flags")


__all__ = [
    "Item",
    "Candidate",
    "MatchedCandidate",
    "PriceRecommendation",
]
