"""
Top‑level package for the Dzukou pricing optimiser.

This package exposes the main modules used throughout the project.  To use the
CLI, invoke ``python -m dzukou_pricer.cli``.  To extend the scraping
functionality, create new classes under ``dzukou_pricer/app/scrape/stores``.
"""

__all__ = [
    "config",
    "types",
    "io",
    "ingest",
    "matching",
    "fx",
    "features",
    "demand",
    "optimize",
    "report",
    "scrape",
]
