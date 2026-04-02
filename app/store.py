import json
from abc import ABC, abstractmethod

import redis

from app.config import REDIS_URL
from app.models import ScoredProduct


class BaseStore(ABC):
    @abstractmethod
    def save_products(self, keyword: str, products: list[ScoredProduct]) -> None:
        pass

    @abstractmethod
    def get_products(self, keyword: str | None = None) -> list[ScoredProduct]:
        pass

    @abstractmethod
    def get_top_products(self, n: int = 3) -> list[ScoredProduct]:
        pass

    @abstractmethod
    def update_product(self, keyword: str, url: str, updates: dict) -> None:
        pass


class RedisStore(BaseStore):
    def __init__(self, redis_url: str = REDIS_URL):
        self.client = redis.from_url(redis_url, decode_responses=True)

    def save_products(self, keyword: str, products: list[ScoredProduct]) -> None:
        key = f"products:{keyword}"
        data = [p.model_dump() for p in products]
        self.client.set(key, json.dumps(data))

    def get_products(self, keyword: str | None = None) -> list[ScoredProduct]:
        if keyword:
            data = self.client.get(f"products:{keyword}")
            if not data:
                return []
            return [ScoredProduct(**p) for p in json.loads(data)]

        all_products = []
        for key in self.client.scan_iter("products:*"):
            data = self.client.get(key)
            if data:
                all_products.extend([ScoredProduct(**p) for p in json.loads(data)])
        return all_products

    def get_top_products(self, n: int = 3) -> list[ScoredProduct]:
        all_products = self.get_products()
        sorted_products = sorted(all_products, key=lambda p: p.score, reverse=True)
        top = sorted_products[:n]
        for i, p in enumerate(top):
            p.rank = i + 1
        return top

    def update_product(self, keyword: str, url: str, updates: dict) -> None:
        products = self.get_products(keyword)
        for i, p in enumerate(products):
            if p.url == url:
                data = p.model_dump()
                data.update(updates)
                products[i] = ScoredProduct(**data)
                break
        self.save_products(keyword, products)
