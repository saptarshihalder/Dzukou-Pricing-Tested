"""
Base classes and utilities for web scraping.

The base scraper performs rate‑limited HTTP requests, respects
robots.txt, supports concurrent fetching and provides helper methods
for building search URLs.  Individual stores should subclass
``BaseScraper`` and implement the ``search`` method.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Optional

import aiohttp
from aiohttp import ClientResponseError
from bs4 import BeautifulSoup

from ..ingest import NormalisedItem
from ..types import Candidate

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter per domain."""

    def __init__(self, rate: float, burst: int = 1) -> None:
        self.rate = rate  # requests per second
        self.burst = burst
        self.tokens = burst
        self.last = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self.lock:
            now = time.monotonic()
            # Refill tokens
            elapsed = now - self.last
            refill = elapsed * self.rate
            self.tokens = min(self.burst, self.tokens + refill)
            if self.tokens < 1:
                # need to wait
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
            self.tokens -= 1.0
            self.last = now


@lru_cache(maxsize=64)
def _parse_robots_txt(domain: str) -> Optional[List[str]]:
    """Fetch and parse robots.txt disallow rules for a domain."""
    import urllib.robotparser as robotparser
    parser = robotparser.RobotFileParser()
    url = f"https://{domain}/robots.txt"
    try:
        parser.set_url(url)
        parser.read()
        rules: List[str] = []
        return rules if parser.can_fetch("*", "/") else None
    except Exception:
        return None


class BaseScraper(ABC):
    """Abstract base class for store scrapers."""

    #: Friendly name for the store
    name: str = "base"
    #: Domain of the store (used for robots and rate limiting)
    domain: str
    #: Base URL for the store
    base_url: str
    #: Search path template; should contain `{query}` placeholder
    search_path: str
    #: Requests per second limit for this domain
    rate_limit_per_sec: float = 1.0

    def __init__(self) -> None:
        self.limiter = RateLimiter(self.rate_limit_per_sec)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession(headers={
                "User-Agent": "Mozilla/5.0 (compatible; DzukouPricer/1.0; +https://example.com)"
            }, timeout=aiohttp.ClientTimeout(total=15))

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    async def _fetch(self, url: str) -> str:
        """Fetch a URL with rate limiting and error handling."""
        # robots.txt check
        rules = _parse_robots_txt(self.domain)
        if rules is None:
            logger.debug("Robots.txt could not be parsed; proceeding anyway for %s", url)
        # Acquire token
        await self.limiter.acquire()
        await self._ensure_session()
        assert self.session
        try:
            async with self.session.get(url, allow_redirects=True) as resp:
                resp.raise_for_status()
                return await resp.text()
        except ClientResponseError as e:
            logger.warning("Request failed: %s %s", e.status, url)
            return ""
        except Exception as e:
            logger.warning("Request error: %s", e)
            return ""

    async def search(self, item: NormalisedItem) -> List[Candidate]:
        """Search for competitor listings for the given item.

        Subclasses must override this method to perform store‑specific
        searches and return a list of :class:`Candidate` objects.  The
        default implementation returns an empty list.
        """
        return []

    async def enrich(self, candidate: Candidate) -> Candidate:
        """Optional enrichment of a candidate listing from its detail page.

        Subclasses can override this to fetch additional fields such
        as shipping costs or VAT inclusions.
        """
        return candidate


class ScraperManager:
    """Manages multiple scrapers and orchestrates concurrent searches."""

    def __init__(self, scrapers: List[BaseScraper], concurrency: int = 10) -> None:
        self.scrapers = scrapers
        self.semaphore = asyncio.Semaphore(concurrency)

    async def _search_store(self, scraper: BaseScraper, item: NormalisedItem) -> List[Candidate]:
        async with self.semaphore:
            return await scraper.search(item)

    async def search_all(self, item: NormalisedItem) -> List[Candidate]:
        """Search all configured stores concurrently for a single item."""
        tasks = [self._search_store(scraper, item) for scraper in self.scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates: List[Candidate] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Scraper error: %s", result)
            else:
                candidates.extend(result)
        return candidates

    async def close_all(self) -> None:
        for scraper in self.scrapers:
            try:
                await scraper.close()
            except Exception:
                pass


__all__ = ["BaseScraper", "ScraperManager"]
