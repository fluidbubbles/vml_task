# Product Intelligence Prototype

**Duration:** 60 Minutes

**Tools Allowed:** Any language, frameworks, and AI tools (e.g., ChatGPT, Claude, Copilot)

**Goal:** Build a working prototype demonstrating scraping, data processing, and UI

---

## Problem Statement

You are building a mini product intelligence tool for an e-commerce use case.

Your task is to:

1. Extract product data (only text – Title, bullet points, description, Price, 5 star rating, number of reviews) for top 20 products coming in search results on Amazon.com for the following keywords
   a. Latest Smart phones
   b. Best laptops for gaming
   c. Shampoo for curly hair
2. Clean and validate the data
3. Transform it into useful insights
4. Expose the data via an API
5. Display results in a simple UI

---

## Tasks

### 1. Data Extraction (Scraping)

Write a script that:

- Loads the product page
- Extracts the fields listed in previous section

Focus on:

- Waiting for elements correctly
- Using robust selectors
- Handling missing or changing elements

You may use: Playwright

### 2. Data Validation & Cleaning

Apply the following rules:

- Remove records with missing title
- Remove records with missing or invalid price
- Remove records with invalid rating
- Handle missing fields gracefully (do not crash)

### 3. Data Transformation

Create the following derived field:

- `score = rating * log(number_of_reviews)`

Then:

- Sort products by score (descending)
- Return top 3 products

### 4. Backend API

Create at least 2 endpoints:

- `/products` → returns cleaned dataset
- `/top-products` → returns top 3 ranked products

You may use:

- Node.js (Express) OR
- Python (FastAPI / Flask)

### 5. Simple UI

Create a minimal UI that:

- Displays the cleaned product list
- Highlights top 3 products

Options:

- React (preferred), OR
- Simple HTML + JavaScript