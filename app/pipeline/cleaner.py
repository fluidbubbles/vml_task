# app/pipeline/cleaner.py
import logging
import re

from app.models import Product, RawProduct

logger = logging.getLogger(__name__)


def clean_products(raw_products: list[RawProduct]) -> list[Product]:
    cleaned = []
    for raw in raw_products:
        try:
            product = _clean_single(raw)
            if product:
                cleaned.append(product)
        except Exception as e:
            logger.warning(f"Dropped product '{raw.title}': {e}")
    return cleaned


def _clean_single(raw: RawProduct) -> Product | None:
    if not raw.title:
        logger.info("Dropped: missing title")
        return None

    price = _parse_price(raw.price)
    if price is None:
        logger.info(f"Dropped '{raw.title}': invalid price '{raw.price}'")
        return None

    rating = _parse_rating(raw.rating)
    if rating is None:
        logger.info(f"Dropped '{raw.title}': invalid rating '{raw.rating}'")
        return None

    num_reviews = _parse_reviews(raw.num_reviews)
    if num_reviews is None:
        logger.info(f"Dropped '{raw.title}': invalid reviews '{raw.num_reviews}'")
        return None

    return Product(
        title=raw.title,
        price=price,
        rating=rating,
        num_reviews=num_reviews,
        bullet_points=raw.bullet_points,
        description=raw.description or "",
        keyword=raw.keyword,
        url=raw.url or "",
    )


def _parse_price(raw: str | None) -> float | None:
    if not raw:
        return None
    # Strip currency symbols/words (USD, EUR, $, etc.)
    cleaned = re.sub(r"[^\d.,\-]", "", raw).strip()
    if "-" in cleaned:
        cleaned = cleaned.split("-")[0].strip()
    # Handle European comma-as-decimal format
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def _parse_rating(raw: str | None) -> float | None:
    if not raw:
        return None
    match = re.search(r"(\d+\.?\d*)", raw)
    if not match:
        return None
    val = float(match.group(1))
    return val if 0 <= val <= 5 else None


def _parse_reviews(raw: str | None) -> int | None:
    if not raw:
        return None
    # Strip parens: "(264)" -> "264"
    cleaned = raw.replace("(", "").replace(")", "").replace(",", "").strip()
    # Handle K suffix: "12.5K" -> 12500
    if cleaned.upper().endswith("K"):
        try:
            val = float(cleaned[:-1]) * 1000
            return int(val) if val > 0 else None
        except ValueError:
            return None
    try:
        val = int(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None
