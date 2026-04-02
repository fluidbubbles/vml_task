import os

KEYWORDS = [
    "Latest Smart phones",
    "Best laptops for gaming",
    "Shampoo for curly hair",
]

AMAZON_BASE_URL = "https://www.amazon.com/s"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

SCRAPE_DELAY_MIN = 2
SCRAPE_DELAY_MAX = 5
REQUEST_TIMEOUT = 10
