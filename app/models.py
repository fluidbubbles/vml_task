from pydantic import BaseModel


class RawProduct(BaseModel):
    title: str | None = None
    price: str | None = None
    rating: str | None = None
    num_reviews: str | None = None
    bullet_points: list[str] = []
    description: str | None = None
    keyword: str
    url: str | None = None


class Product(BaseModel):
    title: str
    price: float
    rating: float
    num_reviews: int
    bullet_points: list[str] = []
    description: str = ""
    keyword: str
    url: str


class ScoredProduct(Product):
    score: float
    rank: int | None = None
