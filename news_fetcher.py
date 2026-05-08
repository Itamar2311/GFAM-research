import requests
from datetime import datetime, timedelta
import streamlit as st

SECTOR_QUERIES = {
    "Infrastructure": [
        "infrastructure investment acquisition private equity",
        "utilities transport energy infrastructure deal",
        "infrastructure fund ownership change capital",
    ],
    "Healthcare Services": [
        "healthcare services acquisition private equity investment",
        "medical services clinic buyout ownership change",
        "healthcare provider capital financing growth",
    ],
    "Financial Services": [
        "financial services fintech acquisition investment",
        "insurance asset management buyout private equity",
        "specialty finance banking deal capital",
    ],
    "Special Situations": [
        "special situations distressed debt restructuring",
        "company restructuring recapitalization private credit",
        "distressed asset acquisition turnaround financing",
    ],
}

def fetch_articles(sector: str, extra_keywords: str, days_back: int) -> list[dict]:
    api_key = st.secrets["GNEWS_API_KEY"]
    queries = SECTOR_QUERIES.get(sector, [sector])

    seen_urls = set()
    all_articles = []

    for base_query in queries:
        query = f"{base_query} {extra_keywords}".strip() if extra_keywords else base_query

        params = {
            "q": query,
            "lang": "en",
            "max": 5,
            "sortby": "relevance",
            "token": api_key,
        }

        try:
            response = requests.get("https://gnews.io/api/v4/search", params=params, timeout=10)
            data = response.json()
        except Exception as e:
            st.warning(f"Request failed: {e}")
            continue

        errors = data.get("errors", [])
        if errors:
            st.warning(f"GNews error: {errors}")
            continue

        for a in data.get("articles", []):
            if not a.get("title") or not a.get("description"):
                continue
            if a["url"] in seen_urls:
                continue

            seen_urls.add(a["url"])
            all_articles.append({
                "title": a["title"],
                "description": a.get("description", "")[:150],
                "source": a.get("source", {}).get("name", ""),
                "url": a["url"],
                "published_at": a.get("publishedAt", "")[:10],
            })

    return all_articles
