# app/worker/tasks.py
import logging

from app.config import AMAZON_BASE_URL
from app.pipeline.cleaner import clean_products
from app.pipeline.transformer import transform_products
from app.scraper.client import HttpScraper
from app.scraper.headers import get_browser_by_index
from app.scraper.parser import parse_product_detail, parse_search_results
from app.store import RedisStore
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)
store = RedisStore()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=5,
    retry_backoff_max=20,
)
def scrape_keyword_task(self, keyword: str):
    logger.info(f"Scraping keyword: {keyword} (attempt {self.request.retries + 1})")

    browser = get_browser_by_index(self.request.retries)
    scraper = HttpScraper(impersonate=browser)

    url = f"{AMAZON_BASE_URL}?k={keyword.replace(' ', '+')}"
    html = scraper.fetch_page(url)
    if not html:
        raise Exception(f"Empty response for keyword: {keyword}")

    raw_products = parse_search_results(html, keyword)
    logger.info(f"Found {len(raw_products)} products for '{keyword}'")

    cleaned = clean_products(raw_products)
    scored = transform_products(cleaned)
    store.save_products(keyword, scored)

    for raw in raw_products:
        if raw.url:
            scrape_detail_task.delay(raw.model_dump(), keyword)

    return {"keyword": keyword, "products_found": len(scored)}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=5,
    retry_backoff_max=20,
)
def scrape_detail_task(self, raw_product_dict: dict, keyword: str):
    url = raw_product_dict.get("url")
    if not url:
        return {"status": "skipped", "reason": "no url"}

    logger.info(f"Fetching detail: {url} (attempt {self.request.retries + 1})")

    browser = get_browser_by_index(self.request.retries)
    scraper = HttpScraper(impersonate=browser)

    html = scraper.fetch_page(url)
    if not html:
        raise Exception(f"Empty response for detail: {url}")

    details = parse_product_detail(html)
    if details:
        store.update_product(keyword, url, details)

    return {"url": url, "enriched_fields": list(details.keys())}
