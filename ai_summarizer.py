import json
import re
import streamlit as st
from groq import Groq

GFAM_GEOGRAPHIES = [
    "Canada", "United States", "UK", "United Kingdom", "Europe",
    "Toronto", "New York", "London", "Chicago", "Boston"
]

GFAM_SECTORS = [
    "infrastructure", "healthcare", "financial services", "fintech",
    "insurance", "asset management", "private equity", "credit",
    "utilities", "energy", "transport", "medical", "rehab"
]

def clean(text):
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def analyze_article(client, article, sector):
    prompt = f"""You are a senior analyst at Genesis Financial Asset Management (GFAM), a Toronto-based private investment firm.

GFAM focuses on {sector}. They provide equity, structured debt, and hybrid capital to support ownership changes and strategic objectives.
Capital products: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital.
Target geographies: North America primarily.

Analyze this news article and respond ONLY with a single JSON object. No markdown, no extra text.

Title: {clean(article['title'])}
Description: {clean(article['description'])}

Return exactly this JSON structure:
{{
  "summary": "2-3 sentences explaining what is happening in this article in plain English",
  "relevance_score": 7,
  "relevance_reason": "1-2 sentences on why this is or is not a fit for GFAM",
  "deal_type": "M&A",
  "companies_mentioned": ["Company A"],
  "locations_mentioned": ["Toronto"],
  "gfam_capital_fit": "Acquisition Financing",
  "investment_rationale": "1-2 sentences on the specific angle GFAM could pursue"
}}

Valid deal_type: M&A, Distressed, Growth, Refinancing, Recapitalization, IPO, Fundraise, Regulatory, Other
Valid gfam_capital_fit: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital, None
relevance_score must be integer 1-10. Score 5+ if related to {sector}, business, or finance."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
    )

    raw = response.choices[0].message.content.strip()

    # Extract JSON object robustly
    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    # Remove control characters that break JSON parsing
    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)

    return json.loads(raw)


def summarize_articles(articles: list[dict], sector: str) -> list[dict]:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    results = []

    for article in articles:
        try:
            ai = analyze_article(client, article, sector)
        except Exception as e:
            ai = {
                "summary": clean(article["description"]),
                "relevance_score": 5,
                "relevance_reason": "Could not parse AI response.",
                "deal_type": "Other",
                "companies_mentioned": [],
                "locations_mentioned": [],
                "gfam_capital_fit": "None",
                "investment_rationale": "",
            }

        locations = ai.get("locations_mentioned", [])
        geo_match = any(
            loc.lower() in g.lower() or g.lower() in loc.lower()
            for loc in locations
            for g in GFAM_GEOGRAPHIES
        )

        sector_tags = [article.get("description", "").lower()]
        sector_match = any(s in " ".join(sector_tags) for s in GFAM_SECTORS)

        results.append({
            **article,
            "gfam_sector": sector,
            "summary": ai.get("summary", clean(article["description"])),
            "relevance_score": ai.get("relevance_score", 5),
            "relevance_reason": ai.get("relevance_reason", ""),
            "deal_type": ai.get("deal_type", "Other"),
            "companies_mentioned": ai.get("companies_mentioned", []),
            "locations_mentioned": locations,
            "gfam_capital_fit": ai.get("gfam_capital_fit", "None"),
            "investment_rationale": ai.get("investment_rationale", ""),
            "sector_tags": [],
            "geo_match": geo_match,
            "sector_match": sector_match,
        })

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results
