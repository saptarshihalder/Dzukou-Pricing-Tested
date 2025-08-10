"""
Product matching heuristics.

This module matches competitor listings to our normalised catalogue
entries using fuzzy string similarity and attribute tolerances.
"""
from __future__ import annotations

from typing import Iterable, List

from rapidfuzz import fuzz  # type: ignore

from .ingest import NormalisedItem
from .types import Candidate, MatchedCandidate


def _string_score(a: str, b: str) -> float:
    """Compute a token sort ratio similarity between two strings."""
    return fuzz.token_sort_ratio(a, b) / 100.0


def _brand_score(item_brand: str | None, candidate_brand: str | None) -> float:
    """Return 1.0 if brands match (case insensitive), else 0.5 if unknown, else 0.0."""
    if not item_brand or not candidate_brand:
        return 0.5
    return 1.0 if item_brand.strip().lower() == candidate_brand.strip().lower() else 0.0


def _size_score(size_item: float | None, size_candidate: str | None) -> float:
    """Assess size similarity within ±10 % tolerance.

    If either size is missing, return 0.5.  If both are present and
    within tolerance, return 1.0; otherwise 0.0.
    """
    if size_item is None or not size_candidate:
        return 0.5
    try:
        # Extract numeric part of candidate size (grams/ml) roughly
        import re

        match = re.search(r"([0-9]+\.?[0-9]*)", size_candidate)
        if not match:
            return 0.0
        qty = float(match.group(1))
        # Very rough: assume candidate size is in same unit as item base size
        # since conversion happened already when scraping
        ratio = qty / size_item
        return 1.0 if 0.9 <= ratio <= 1.1 else 0.0
    except Exception:
        return 0.0


def match_candidates(
    item: NormalisedItem, candidates: Iterable[Candidate]
) -> List[MatchedCandidate]:
    """Match a normalised catalogue item against a list of competitor candidates.

    Each candidate is scored based on string similarity, brand match
    and size tolerance.  The resulting match score is the average of
    these factors.  Candidates with a score below 0.3 are discarded.

    :param item: The normalised item being matched.
    :param candidates: Iterable of competitor listings.
    :returns: List of :class:`MatchedCandidate` sorted by decreasing score.
    """
    matched: List[MatchedCandidate] = []
    for cand in candidates:
        title_score = _string_score(item.fingerprint, " ".join(
            filter(None, [cand.brand or "", cand.title, cand.size or "", cand.url])
        ))
        brand_score = _brand_score(item.item.brand, cand.brand)
        size_score = _size_score(item.size_in_base_units, cand.size)
        # Weighted average; emphasise title similarity
        score = 0.6 * title_score + 0.2 * brand_score + 0.2 * size_score
        if score >= 0.3:
            matched.append(MatchedCandidate(candidate=cand, match_score=score))
    # Sort by descending score
    matched.sort(key=lambda m: m.match_score, reverse=True)
    return matched


__all__ = ["match_candidates"]
