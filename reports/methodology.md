# Methodology

This document describes the simplified pricing pipeline implemented in `pricing_pipeline.py`.

1. **Data ingestion**: the source CSV is downloaded and cleaned. Numeric price fields are parsed after removing stray characters.
2. **Competitor prices**: competitor prices are simulated for demonstration purposes. In production these would be gathered from retailer websites or APIs.
3. **Demand model**: assumes constant price elasticity of -1.5 and a baseline demand of 100 units at the current price.
4. **Optimization**: prices are optimized over a grid with psychological price endings and constrained by competitor prices and margin floors.
5. **Outputs**: JSON snapshot of competitor prices, CSV of recommendations, and this report are generated in the `data/` and `reports/` directories.

The generated recommendations are illustrative only and not based on live data.

## Refresh cadence

Scrape competitor prices daily and rerun the optimization weekly:

```
# daily competitor scrape
0 6 * * * python pricing_pipeline.py
```

The example cron job above runs every day at 06:00 UTC.
