"""
Reporting utilities.

This module transforms optimisation results into human‑readable
Markdown reports as well as machine‑readable JSON and CSV files.  The
Markdown report summarises global statistics and provides per‑item
recommendations with competitor comparison tables.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .features import price_ending_feature
from .types import MatchedCandidate, PriceRecommendation


def _format_competitor_table(cands: List[MatchedCandidate]) -> str:
    """Format a Markdown table of competitor listings for one item."""
    if not cands:
        return "No competitor data available."
    lines = ["| Store | Price | Stock | Match Score |", "|---|---|---|---|"]
    for mc in cands[:10]:  # limit to first 10 to avoid unwieldy tables
        store = mc.candidate.store
        price = f"{mc.effective_price:.2f}" if mc.effective_price else "-"
        stock = mc.candidate.stock or "-"
        score = f"{mc.match_score:.2f}"
        lines.append(f"| {store} | {price} | {stock} | {score} |")
    return "\n".join(lines)


def generate_markdown_report(
    results: List[PriceRecommendation],
) -> str:
    """Generate a Markdown report summarising pricing recommendations."""
    lines: List[str] = []
    lines.append("# Pricing Recommendation Report\n")
    # Global summary
    increases = sum(
        1 for r in results if r.recommended_price is not None and r.current_price and r.recommended_price > r.current_price
    )
    decreases = sum(
        1 for r in results if r.recommended_price is not None and r.current_price and r.recommended_price < r.current_price
    )
    total_items = len(results)
    lines.append(f"**Items analysed:** {total_items}\n")
    lines.append(f"**Price increases:** {increases}\n")
    lines.append(f"**Price decreases:** {decreases}\n")
    # Per item sections
    for r in results:
        lines.append(f"\n## Item: {r.item_id} — {r.item_id}\n")
        lines.append(f"Current price: {r.current_price if r.current_price is not None else 'N/A'} {r.currency}")
        lines.append(
            f"Recommended price: {r.recommended_price if r.recommended_price is not None else 'N/A'} {r.currency}\n"
        )
        if r.expected_profit is not None:
            lines.append(f"Expected profit: {r.expected_profit:.2f} {r.currency}\n")
        if r.profit_uplift_vs_current_pct is not None:
            lines.append(
                f"Profit uplift vs current: {r.profit_uplift_vs_current_pct:.2f}%\n"
            )
        if r.demand_lift_vs_current_pct is not None:
            lines.append(
                f"Demand uplift vs current: {r.demand_lift_vs_current_pct:.2f}%\n"
            )
        if r.rationale:
            lines.append(f"**Rationale:** {r.rationale}\n")
        # Competitor table
        lines.append("\nCompetitor comparison:\n")
        lines.append(_format_competitor_table(r.competitor_summary))
    return "\n".join(lines)


__all__ = ["generate_markdown_report"]
