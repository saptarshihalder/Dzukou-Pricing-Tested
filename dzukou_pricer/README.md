# Dzukou Pricer

This project is a pricing optimisation toolkit for sustainable e ec‑commerce.  
Given a catalogue of products, competitor pricing information is scraped from a
wide variety of ethical retail stores and used to recommend profitable yet
competitive prices.  
The toolchain is built to be asynchronous, robust and reproducible. It
implements the following pipeline:

1. **Ingest & normalise** your catalogue CSV (detect columns, standardise
   units and build canonical product fingerprints).
2. **Concurrent multi‑store scraping** across dozens of partner shops
   (including Shopify storefronts). Each store implements a small scraper
   derived from `BaseScraper`, which handles rate limiting, robots.txt
   checks and both static and dynamic page parsing.
3. **Product matching** using fuzzy string matching and attribute
   tolerance to associate competitor listings with your products.
4. **Currency conversion** using live exchange rates (with a static
   fallback) to compare prices in a single currency.
5. **Feature engineering** to build explanatory variables such as
   competitor price index, spread and brand strength proxies.
6. **Demand modelling** using either a simple elastic demand curve or
   hierarchical modelling if historical sales data are available.
7. **Profit optimisation** that respects margin floors, psychological
   price endings and competitive guardrails.  
8. **Reporting** that produces machine‑readable JSON, CSV exports and a
   human‑readable Markdown report summarising recommendations.

The codebase is organised into clearly delineated modules under
`dzukou_pricer/app`.  A simple CLI built with [Typer](https://typer.tiangolo.com/)
orchestrates the end‑to‑end run.

## Quick start

Install the dependencies (preferably into a virtual environment):

```bash
python -m pip install -r requirements.txt
```

Run a pricing run against your CSV. The following example targets US
and EU markets with a 10 % margin floor and a concurrency of 20
requests:

```bash
python -m dzukou_pricer.cli run \
  --csv "https://.../Dzukou_Pricing_Overview_With_Names%20-%20Copy.csv" \
  --markets US EU \
  --margin-floor 0.10 \
  --concurrency 20 \
  --headless true
```

Outputs are written into the `data/`, `logs/` and `reports/` folders.  A
per‑item JSON and CSV summary plus a human‑readable Markdown report will
be produced, along with a raw scrape log.

## Extending

To add support for a new store, subclass `BaseScraper` and implement
the `search` and (optionally) `enrich` methods in
`dzukou_pricer/app/scrape/stores/yourstore.py`.  See existing scraper
modules for examples.  Ensure you respect robots.txt directives and
avoid scraping sites where scraping is disallowed.  Add your scraper
class to the mapping in `dzukou_pricer/app/scrape/__init__.py`.

If you have historical sales data, integrate it into the demand model
via `dzukou_pricer/app/demand.py`.  The default model will fall back
to category priors when no sales history is available.
