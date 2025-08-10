"""
Initialise scraper package.

This module exposes a dictionary of available store scrapers keyed by
store name.  To add a new store, create a corresponding module in
``dzukou_pricer/app/scrape/stores`` and add it to this mapping.
"""
from __future__ import annotations

from typing import Dict, Type

from .base import BaseScraper

# Import all store scraper classes here
from .stores.madetrade import MadeTradeScraper
from .stores.earthhero import EarthHeroScraper
from .stores.goodee import GoodeeScraper
from .stores.packagefree import PackageFreeScraper
from .stores.thecitizenry import TheCitizenryScraper
from .stores.tenthousandvillages import TenThousandVillagesScraper
from .stores.novica import NovicaScraper
from .stores.thelittlemarket import TheLittleMarketScraper
from .stores.donegood import DoneGoodScraper
from .stores.folksy import FolksyScraper
from .stores.indiecart import IndieCartScraper
from .stores.zerowaste import ZeroWasteScraper
from .stores.ecoroots import EcoRootsScraper
from .stores.wildminimalist import WildMinimalistScraper
from .stores.greenecodream import GreenEcoDreamScraper


SCRAPERS: Dict[str, Type[BaseScraper]] = {
    "Made Trade": MadeTradeScraper,
    "EarthHero": EarthHeroScraper,
    "GOODEE": GoodeeScraper,
    "Package Free Shop": PackageFreeScraper,
    "The Citizenry": TheCitizenryScraper,
    "Ten Thousand Villages": TenThousandVillagesScraper,
    "NOVICA": NovicaScraper,
    "The Little Market": TheLittleMarketScraper,
    "DoneGood": DoneGoodScraper,
    "Folksy": FolksyScraper,
    "IndieCart": IndieCartScraper,
    "Zero Waste Store": ZeroWasteScraper,
    "EcoRoots": EcoRootsScraper,
    "Wild Minimalist": WildMinimalistScraper,
    "Green Eco Dream": GreenEcoDreamScraper,
}

__all__ = ["SCRAPERS"]
