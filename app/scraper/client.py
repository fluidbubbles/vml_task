# app/scraper/client.py
import random
import time
from abc import ABC, abstractmethod

import requests

from app.config import REQUEST_TIMEOUT, SCRAPE_DELAY_MAX, SCRAPE_DELAY_MIN
from app.scraper.headers import get_random_headers


class BaseScraper(ABC):
    @abstractmethod
    def fetch_page(self, url: str) -> str | None:
        """Fetch a URL and return HTML content, or None on failure."""
        pass


class HttpScraper(BaseScraper):
    def __init__(self):
        self.session = requests.Session()

    def fetch_page(self, url: str) -> str | None:
        delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
        time.sleep(delay)

        headers = get_random_headers()
        self.session.headers.update(headers)

        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
