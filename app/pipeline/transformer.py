# app/pipeline/transformer.py
import math

from app.models import Product, ScoredProduct


def transform_products(products: list[Product]) -> list[ScoredProduct]:
    scored = []
    for p in products:
        score = p.rating * math.log(p.num_reviews) if p.num_reviews > 0 else 0.0
        scored.append(ScoredProduct(**p.model_dump(), score=score))

    scored.sort(key=lambda x: x.score, reverse=True)

    for i, p in enumerate(scored[:3]):
        p.rank = i + 1

    return scored
