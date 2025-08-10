"""
Command‑line interface for the Dzukou pricing optimiser.

This module defines a CLI using Typer.  The primary command ``run``
executes the full pipeline: ingest, scrape, match, model, optimise and
report.  It writes outputs into timestamped files under ``data/``,
``logs/`` and ``reports/``.
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import json
from typing import List, Optional

import typer

from .config import DEFAULT_CONCURRENCY, DEFAULT_MARGIN_FLOOR, BASE_CURRENCY
from .demand import get_elasticity
from .features import compute_competitor_features
from .fx import convert
from .ingest import normalise_items
from .io import read_catalog, write_csv, write_json, write_markdown
from .matching import match_candidates
from .optimize import optimise_price
from .report import generate_markdown_report
from .scrape import SCRAPERS
from .scrape.base import ScraperManager
from .types import MatchedCandidate, PriceRecommendation


app = typer.Typer(add_completion=False)


def _current_timestamp() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


@app.command()
def run(
    csv: str = typer.Option(..., help="Path or URL to the catalogue CSV"),
    markets: List[str] = typer.Option([BASE_CURRENCY], help="Target markets/currencies"),
    margin_floor: float = typer.Option(DEFAULT_MARGIN_FLOOR, help="Minimum margin above COGS (fraction)"),
    concurrency: int = typer.Option(DEFAULT_CONCURRENCY, help="Max concurrent requests across stores"),
    headless: bool = typer.Option(True, help="Reserved for enabling JS rendering (unused)"),
) -> None:
    """Run the pricing optimisation pipeline."""
    # Load catalogue
    items = read_catalog(csv)
    normalised_items = normalise_items(items)
    # Instantiate scrapers
    scraper_instances = [cls() for cls in SCRAPERS.values()]
    manager = ScraperManager(scraper_instances, concurrency=concurrency)
    results: List[PriceRecommendation] = []

    async def process_item(nitem):
        # Scrape competitors
        candidates = await manager.search_all(nitem)
        # Match candidates
        matched = match_candidates(nitem, candidates)
        # Convert prices to base currency
        for mc in matched:
            price = mc.candidate.shelf_price
            if price is not None and mc.candidate.currency:
                mc.effective_price = convert(price, mc.candidate.currency, BASE_CURRENCY)
            else:
                mc.effective_price = None
        # Compute features
        feats = compute_competitor_features(nitem.item.current_price, matched)
        # Determine elasticity
        elasticity = get_elasticity(nitem.item)
        # Optimise price
        cogs = nitem.item.cogs or 0.0
        current_price = nitem.item.current_price
        best_price, best_units, best_profit, profit_uplift, demand_uplift = optimise_price(
            cogs=cogs or 0.0,
            elasticity=elasticity,
            current_price=current_price,
            competitor_min_price=feats.get("min_competitor"),
            margin_floor=margin_floor,
            baseline_units=100.0,
            price_step=0.50,
        )
        # Build rationale
        rationale = (
            f"Set price to {best_price:.2f} {BASE_CURRENCY} to achieve estimated profit of {best_profit:.2f}"
        )
        # Build PriceRecommendation
        rec = PriceRecommendation(
            item_id=nitem.item.item_id,
            current_price=current_price,
            recommended_price=best_price,
            currency=BASE_CURRENCY,
            expected_units=best_units,
            expected_profit=best_profit,
            profit_uplift_vs_current_pct=profit_uplift,
            demand_lift_vs_current_pct=demand_uplift,
            competitor_summary=matched,
            rationale=rationale,
            confidence="medium",
            flags=[],
        )
        results.append(rec)

    async def run_all():
        tasks = [process_item(item) for item in normalised_items]
        await asyncio.gather(*tasks)
        await manager.close_all()

    asyncio.run(run_all())
    # Write outputs
    timestamp = _current_timestamp()
    # JSON export
    json_path = f"data/competitor_prices_{timestamp}.json"
    write_json(json_path, [r.dict() for r in results])
    # CSV export: flatten per‑item summary
    csv_rows = []
    headers = [
        "item_id",
        "item_name",
        "current_price",
        "recommended_price",
        "expected_units",
        "expected_profit",
        "min_competitor",
        "median_competitor",
        "undercut_pct",
    ]
    for r in results:
        features = compute_competitor_features(r.current_price, r.competitor_summary)
        csv_rows.append({
            "item_id": r.item_id,
            "item_name": next((ni.item.item_name for ni in normalised_items if ni.item.item_id == r.item_id), r.item_id),
            "current_price": r.current_price,
            "recommended_price": r.recommended_price,
            "expected_units": r.expected_units,
            "expected_profit": r.expected_profit,
            "min_competitor": features.get("min_competitor"),
            "median_competitor": features.get("median_competitor"),
            "undercut_pct": features.get("undercut_pct"),
        })
    csv_path = f"data/recommendations_{timestamp}.csv"
    write_csv(csv_path, csv_rows, headers)
    # Markdown report
    md_content = generate_markdown_report(results)
    md_path = f"reports/PRICE_REPORT_{timestamp}.md"
    write_markdown(md_path, md_content)
    typer.echo(f"Results saved to {json_path}, {csv_path} and {md_path}")


if __name__ == "__main__":  # pragma: no cover
    app()
