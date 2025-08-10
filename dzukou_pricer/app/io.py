"""
I/O utilities for the Dzukou pricing optimiser.

This module handles reading the input CSV, writing outputs (JSON, CSV and
Markdown) and creating necessary directories.  It hides the details of
Pandas and JSON serialisation from the rest of the codebase.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

from .types import Item, PriceRecommendation


def read_catalog(csv_path: str) -> List[Item]:
    """Read a catalogue CSV into a list of :class:`Item` objects.

    The function attempts to normalise column names to a canonical set.

    :param csv_path: Path or URL to the CSV file.
    :returns: List of items.
    """
    # Pandas can read URLs directly
    df = pd.read_csv(csv_path)
    # Normalize column names: lower case and strip whitespace
    df.columns = [c.strip().lower() for c in df.columns]
    # Map known column aliases to canonical names
    column_map = {
        "id": "item_id",
        "sku": "item_id",
        "name": "item_name",
        "title": "item_name",
        "brand_name": "brand",
        "cost": "cogs",
        "cogs": "cogs",
        "current_price": "current_price",
        "price": "current_price",
        "currency": "currency",
        "category": "category",
        "size": "size",
        "pack": "pack_count",
        "pack_count": "pack_count",
    }
    # Build a canonical DataFrame
    canonical = {}
    for col_alias, canonical_name in column_map.items():
        if col_alias in df.columns:
            canonical.setdefault(canonical_name, df[col_alias])
    canonical_df = pd.DataFrame(canonical)
    items: List[Item] = []
    for row in canonical_df.itertuples(index=False):
        data = row._asdict()
        # Ensure numeric values are floats
        if data.get("cogs") is not None:
            try:
                data["cogs"] = float(data["cogs"])
            except (TypeError, ValueError):
                data["cogs"] = None
        if data.get("current_price") is not None:
            try:
                data["current_price"] = float(data["current_price"])
            except (TypeError, ValueError):
                data["current_price"] = None
        # Pack count may be float or string; convert to int if possible
        if data.get("pack_count") is not None:
            try:
                data["pack_count"] = int(float(data["pack_count"]))
            except (TypeError, ValueError):
                data["pack_count"] = None
        items.append(Item(**data))
    return items


def ensure_dir(path: str) -> None:
    """Ensure that a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def write_json(path: str, data: Iterable[dict]) -> None:
    """Write an iterable of dictionaries to a JSON file."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, indent=2)


def write_csv(path: str, rows: Iterable[dict], header: Sequence[str]) -> None:
    """Write a CSV file from a sequence of dictionaries."""
    ensure_dir(os.path.dirname(path))
    df = pd.DataFrame(list(rows), columns=header)
    df.to_csv(path, index=False)


def write_markdown(path: str, content: str) -> None:
    """Write a Markdown string to a file."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


__all__ = [
    "read_catalog",
    "ensure_dir",
    "write_json",
    "write_csv",
    "write_markdown",
]
