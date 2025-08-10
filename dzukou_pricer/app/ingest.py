"""
Ingestion and normalisation of catalogue data.

The functions in this module load raw catalogue items and attempt to
standardise size and pack information into comparable units.  They also
build canonical product fingerprints used to match competitor listings.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .types import Item


SIZE_PATTERN = re.compile(
    r"(?P<qty>[0-9\.]+)\s*(?P<unit>g|kg|ml|l|oz|fl oz|lb|pound|gm|gram|grams|litre|liter)"
)


def parse_size(size_str: str) -> Optional[float]:
    """Attempt to parse a size string into a numeric quantity in grams/ml.

    The function currently converts:

    * grams (g) and kilograms (kg) into grams
    * millilitres (ml) and litres (l) into millilitres
    * ounces (oz) and fluid ounces (fl oz) into grams (assumes 28.35 g per oz)
    * pounds (lb) into grams (453.59 g)

    :returns: The numeric size in base units (grams or ml) or None if
              parsing fails.
    """
    if not size_str:
        return None
    match = SIZE_PATTERN.search(size_str.lower())
    if not match:
        return None
    qty = float(match.group("qty"))
    unit = match.group("unit")
    if unit in {"g", "gm", "gram", "grams"}:
        return qty
    if unit == "kg":
        return qty * 1000.0
    if unit in {"ml"}:
        return qty
    if unit in {"l", "litre", "liter"}:
        return qty * 1000.0
    if unit in {"oz", "fl oz"}:
        return qty * 28.35
    if unit in {"lb", "pound"}:
        return qty * 453.59
    return None


def build_fingerprint(item: Item) -> str:
    """Construct a canonical fingerprint for an item.

    The fingerprint is used to match competitor listings and consists of
    normalised brand, title and size attributes in lower case.
    """
    parts = []
    if item.brand:
        parts.append(item.brand.strip().lower())
    parts.append(item.item_name.strip().lower())
    if item.size:
        parts.append(item.size.strip().lower())
    if item.pack_count:
        parts.append(str(item.pack_count))
    return "|".join(parts)


@dataclass
class NormalisedItem:
    """Internal representation of an item with derived attributes."""

    item: Item
    fingerprint: str
    size_in_base_units: Optional[float]


def normalise_items(items: List[Item]) -> List[NormalisedItem]:
    """Normalise a list of items.

    :param items: Raw items from the catalogue.
    :returns: A list of :class:`NormalisedItem` with parsed sizes and fingerprints.
    """
    normalised: List[NormalisedItem] = []
    for item in items:
        size_base = None
        if item.size:
            size_base = parse_size(str(item.size))
        fp = build_fingerprint(item)
        normalised.append(NormalisedItem(item=item, fingerprint=fp, size_in_base_units=size_base))
    return normalised


__all__ = [
    "parse_size",
    "build_fingerprint",
    "NormalisedItem",
    "normalise_items",
]
