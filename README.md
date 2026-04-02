# Product Intelligence Prototype

A mini product intelligence tool for e-commerce that scrapes Amazon product data across multiple search keywords, cleans and validates it, computes ranking scores, and serves results via a REST API with a web UI.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Web Framework | FastAPI + Uvicorn |
| Task Queue | Celery |
| Broker / Store | Redis |
| Scraping | requests + BeautifulSoup4 |
| Validation | Pydantic |
| Containerization | Docker + Docker Compose |
| Frontend | Vanilla HTML + JS |
| Package Manager | Poetry |

## Architecture Overview

The system uses a **decoupled job-based pipeline** with Celery for fault isolation. Each search keyword and each product detail fetch runs as an independent task with automatic retries and header rotation.

```
                          ┌──────────────────────────────────────────────────┐
                          │                  Docker Compose                  │
                          │                                                  │
  ┌──────────┐            │  ┌────────────────────────────────────────────┐  │
  │  Browser  │◄──HTML────│──│  FastAPI (Uvicorn) :8000                   │  │
  │           │──/scrape──│─►│                                            │  │
  │  index.   │◄──JSON────│──│  GET  /products?keyword=                   │  │
  │  html     │           │  │  GET  /top-products                        │  │
  └──────────┘            │  │  POST /scrape                              │  │
                          │  │  GET  / (static HTML)                      │  │
                          │  └────────┬──────────────────────┬────────────┘  │
                          │           │ enqueues tasks        │ reads data   │
                          │           ▼                       ▼              │
                          │  ┌────────────────┐    ┌─────────────────────┐  │
                          │  │  Celery Worker  │    │   Redis :6379       │  │
                          │  │  concurrency=2  │◄──►│                     │  │
                          │  │                 │    │   • Task broker      │  │
                          │  │  keyword tasks  │    │   • Result backend   │  │
                          │  │  detail tasks   │    │   • Product store    │  │
                          │  └───────┬─────────┘    └─────────────────────┘  │
                          │          │                                        │
                          └──────────┼────────────────────────────────────────┘
                                     │ HTTP + header rotation
                                     ▼
                            ┌──────────────────┐
                            │   Amazon.com      │
                            │   Search pages    │
                            │   Detail pages    │
                            └──────────────────┘
```

## Data Flow Pipeline

```
  ┌─────────────┐     ┌───────────────┐     ┌──────────────┐     ┌─────────────┐
  │   Scraper    │────►│   Cleaner     │────►│  Transformer │────►│  RedisStore  │
  │              │     │               │     │              │     │              │
  │ HTTP fetch   │     │ Parse price   │     │ score =      │     │ save_products│
  │ BS4 parse    │     │ Parse rating  │     │   rating *   │     │ get_products │
  │ header       │     │ Parse reviews │     │   log(reviews)│    │ get_top (3)  │
  │ rotation     │     │ Drop invalid  │     │ Rank top 3   │     │ update detail│
  └─────────────┘     └───────────────┘     └──────────────┘     └─────────────┘
       │                                                                │
  RawProduct ──────► Product ──────► ScoredProduct ───────────► ScoredProduct
  (all optional)     (validated)     (+ score, rank)            (persisted)
```

## Celery Task Flow

```
  POST /scrape
       │
       ├── scrape_keyword_task("Latest Smart phones")
       ├── scrape_keyword_task("Best laptops for gaming")    ← 3 independent jobs
       └── scrape_keyword_task("Shampoo for curly hair")
                │
                │  For each keyword:
                │  1. Fetch Amazon search page
                │  2. Parse up to 20 product cards
                │  3. Clean → Transform → Store
                │  4. Enqueue detail tasks:
                │
                ├── scrape_detail_task(product_1)
                ├── scrape_detail_task(product_2)    ← up to 20 per keyword
                ├── ...                                (independent, enriches
                └── scrape_detail_task(product_20)      bullet points + description)

  Retry policy: 3 retries, exponential backoff (5s → 10s → 20s)
  Header profile rotates on each retry attempt
```

## Module Structure

```
vml_task/
├── app/
│   ├── __init__.py
│   ├── config.py               # Keywords, delays, URLs, Redis config
│   ├── models.py               # Pydantic: RawProduct → Product → ScoredProduct
│   ├── store.py                # BaseStore ABC + RedisStore implementation
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── headers.py          # 5 browser header profiles, UA rotation
│   │   ├── client.py           # BaseScraper ABC + HttpScraper (requests)
│   │   └── parser.py           # BS4 parsing: search results + detail pages
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── cleaner.py          # Validate & clean: RawProduct → Product
│   │   └── transformer.py     # Score calc (rating * log(reviews)), ranking
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # FastAPI endpoints
│   └── worker/
│       ├── __init__.py
│       ├── celery_app.py       # Celery config (Redis broker + backend)
│       └── tasks.py            # scrape_keyword_task, scrape_detail_task
├── static/
│   └── index.html              # Frontend UI (vanilla JS)
├── main.py                     # FastAPI entry point
├── pyproject.toml              # Poetry dependencies
├── Dockerfile                  # Single image (API + worker)
└── docker-compose.yml          # Redis, API, Worker services
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the HTML frontend |
| `GET` | `/products` | All cleaned & scored products. Optional `?keyword=` filter |
| `GET` | `/top-products` | Top 3 products ranked by score |
| `POST` | `/scrape` | Triggers Celery scrape jobs for all 3 keywords |

## Data Models

```
RawProduct (from scraper)        Product (validated)           ScoredProduct (ranked)
─────────────────────────        ──────────────────            ────────────────────────
title: str | None                title: str (required)         ... inherits Product ...
price: str | None                price: float (> 0)            score: float
rating: str | None               rating: float (0-5)           rank: int | None (1-3)
num_reviews: str | None          num_reviews: int (> 0)
bullet_points: list[str]         bullet_points: list[str]
description: str | None          description: str
keyword: str                     keyword: str
url: str | None                  url: str
```

## Decoupling & Extensibility

All layers communicate through abstract interfaces:

- **`BaseStore`** ABC — `save_products()`, `get_products()`, `get_top_products()`, `update_product()`. Redis implementation provided; swappable for Postgres, MongoDB, etc.
- **`BaseScraper`** ABC — `fetch_page(url) → str`. HTTP/requests implementation provided; swappable for Playwright (phase 2) or any other strategy.
- **Pipeline** — pure functions operating on Pydantic models. No knowledge of data source or destination.
- **API** — depends on `BaseStore` interface, not Redis directly.

## Fault Isolation

- **Keyword-level**: Each keyword scrape is an independent Celery task. One keyword failing doesn't affect others.
- **Product-level**: Each product detail fetch is independent. Failure leaves the product with search-page data only.
- **Retry with rotation**: 3 retries with exponential backoff. Header profile rotates on each retry to avoid detection patterns.

## Quick Start

```bash
# Build and start all services
docker-compose up --build -d

# Verify API
curl http://localhost:8000/products          # → [] (empty, no scrape yet)

# Trigger scraping
curl -X POST http://localhost:8000/scrape    # → {"status": "started", "tasks": [...]}

# Check results (~30s later)
curl http://localhost:8000/products
curl http://localhost:8000/top-products

# Open UI
open http://localhost:8000/
```

## Search Keywords

The system scrapes Amazon for these 3 queries (configurable in `app/config.py`):

1. Latest Smart phones
2. Best laptops for gaming
3. Shampoo for curly hair

Each returns up to 20 products, yielding a maximum of 60 products total.

## Scoring Formula

```
score = rating * ln(num_reviews)
```

Products are sorted by score descending, and the top 3 are tagged with ranks 1-3. This formula balances quality (rating) with popularity (review volume), using the logarithm to dampen the effect of very high review counts.
