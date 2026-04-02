import logging
import re

from bs4 import BeautifulSoup

from app.models import RawProduct

logger = logging.getLogger(__name__)


def parse_search_results(html: str, keyword: str) -> list[RawProduct]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    results = soup.select('div[data-component-type="s-search-result"]')
    for result in results[:20]:
        try:
            product = _parse_search_card(result, keyword)
            products.append(product)
        except Exception as e:
            logger.warning(f"Failed to parse product card: {e}")
            continue

    return products


def _parse_search_card(card, keyword: str) -> RawProduct:
    title = None
    title_el = card.select_one("h2 span")
    if title_el:
        title = title_el.get_text(strip=True)

    url = None
    link_el = card.select_one("a.a-link-normal.s-no-outline")
    if not link_el:
        link_el = card.select_one("h2 a")
    if link_el and link_el.get("href"):
        href = link_el["href"]
        if href.startswith("/"):
            url = f"https://www.amazon.com{href}"
        else:
            url = href

    price = None
    price_el = card.select_one("span.a-price > span.a-offscreen")
    if price_el:
        price = price_el.get_text(strip=True)

    rating = None
    rating_el = card.select_one("span.a-icon-alt")
    if rating_el:
        rating = rating_el.get_text(strip=True)

    num_reviews = None
    reviews_el = card.select_one('a[href*="customerReviews"] span')
    if not reviews_el:
        reviews_el = card.select_one('span[aria-label*="stars"] + span a span')
    if reviews_el:
        num_reviews = reviews_el.get_text(strip=True)

    return RawProduct(
        title=title,
        price=price,
        rating=rating,
        num_reviews=num_reviews,
        keyword=keyword,
        url=url,
    )


def parse_product_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    try:
        bullets_el = soup.select_one("#feature-bullets")
        if bullets_el:
            result["bullet_points"] = [
                li.get_text(strip=True)
                for li in bullets_el.select("li span.a-list-item")
                if li.get_text(strip=True)
            ]
    except Exception as e:
        logger.warning(f"Failed to parse bullet points: {e}")

    try:
        desc_el = soup.select_one("#productDescription")
        if desc_el:
            result["description"] = desc_el.get_text(strip=True)
    except Exception as e:
        logger.warning(f"Failed to parse description: {e}")

    return result
