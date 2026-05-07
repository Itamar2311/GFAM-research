import streamlit as st
import pandas as pd
from datetime import datetime
from news_fetcher import fetch_articles
from ai_summarizer import summarize_articles
from report_generator import generate_report

st.set_page_config(page_title="GFAM Deal Flow Monitor", page_icon="📡", layout="wide")

st.title("📡 GFAM Deal Flow Monitor")
st.caption("AI-powered deal sourcing for Genesis Financial Asset Management")
st.divider()

with st.sidebar:
    st.header("🔎 Search Criteria")
    sector = st.selectbox("Sector", ["Infrastructure", "Healthcare Services", "Financial Services", "Special Situations"])
    keywords = st.text_input("Additional keywords (optional)", placeholder="e.g. acquisition, buyout")
    days_back = st.slider("Days back", 1, 14, 3)
    min_score = st.slider("Minimum relevance score", 1, 10, 4)
    run = st.button("🔍 Find Deals", use_container_width=True)

DEAL_TYPE_COLORS = {
    "M&A": "🔵", "Distressed": "🔴", "Growth": "🟢",
    "Refinancing": "🟡", "Recapitalization": "🟠",
    "IPO": "🟣", "Fundraise": "⚪", "Regulatory": "⬛", "Other": "⬜"
}

def to_csv(results):
    rows = []
    for r in results:
        rows.append({
            "Sector": r["gfam_sector"],
            "Title": r["title"],
            "Source": r["source"],
            "Published": r["published_at"],
            "Relevance Score": r["relevance_score"],
            "Deal Type": r["deal_type"],
            "GFAM Capital Fit": r["gfam_capital_fit"],
            "Summary": r["summary"],
            "Relevance Reason": r["relevance_reason"],
            "Investment Rationale": r["investment_rationale"],
            "Companies Mentioned": ", ".join(r["companies_mentioned"]),
            "Locations": ", ".join(r["locations_mentioned"]),
            "Geo Match": "Yes" if r["geo_match"] else "No",
            "URL": r["url"],
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")

if run:
    with st.spinner("Fetching latest news..."):
        articles = fetch_articles(sector, keywords, days_back)

    if not articles:
        st.warning("No articles found. Try different keywords or a wider date range.")
    else:
        st.success(f"Found {len(articles)} articles. Running AI analysis...")
        with st.spinner("Analyzing with AI..."):
            results = summarize_articles(articles, sector)

        # Filter only by score — no geo filter
        filtered = [r for r in results if r["relevance_score"] >= min_score]
        dropped = len(results) - len(filtered)

        if not filtered:
            st.warning("No articles passed filters. Try lowering the minimum score.")
            st.write("Score breakdown:")
            for r in results:
                st.write(f"Score {r['relevance_score']} — {r['title'][:60]}")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Relevant articles", len(filtered))
            col2.metric("Avg relevance", f"{sum(r['relevance_score'] for r in filtered)/len(filtered):.1f}/10")
            col3.metric("Geo matches", sum(1 for r in filtered if r["geo_match"]))
            col4.metric("Filtered out", dropped)

            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label="📥 Export to CSV",
                    data=to_csv(filtered),
                    file_name=f"GFAM_deals_{sector.replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with exp_col2:
                try:
                    report_bytes = generate_report(filtered)
                    st.download_button(
                        label="📄 Download Daily Report (.docx)",
                        data=report_bytes,
                        file_name=f"GFAM_Daily_Briefing_{datetime.now().strftime('%Y-%m-%d')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Report generation failed: {e}")

            st.divider()
            st.subheader(f"Results — {sector}")

            for item in filtered:
                score = item["relevance_score"]
                color = "🟢" if score >= 7 else "🟡"
                deal_icon = DEAL_TYPE_COLORS.get(item["deal_type"], "⬜")
                geo_tag = " 🌍" if item["geo_match"] else ""

                with st.expander(f"{color} [{score}/10] {deal_icon} {item['deal_type']}{geo_tag}  —  {item['title']}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown("**Summary**")
                        st.write(item["summary"])
                        st.markdown("**Why it's relevant to GFAM**")
                        st.write(item["relevance_reason"])
                        st.markdown("**💡 Investment rationale**")
                        st.info(item["investment_rationale"] or "N/A")

                    with col2:
                        st.markdown("**Capital fit**")
                        st.success(item["gfam_capital_fit"])
                        st.markdown("**Deal type**")
                        st.write(item["deal_type"])

                        if item["companies_mentioned"]:
                            st.markdown("**Companies mentioned**")
                            st.write(", ".join(item["companies_mentioned"]))

                        if item["locations_mentioned"]:
                            st.markdown("**Locations**")
                            st.write(", ".join(item["locations_mentioned"]))
                            st.caption("✅ GFAM geography" if item["geo_match"] else "⚠️ Outside target geo")

                        st.markdown("**Source**")
                        st.write(f"{item['source']} · {item['published_at']}")
                        st.link_button("Read article", item["url"])

else:
    st.info("👈 Set your search criteria in the sidebar and click **Find Deals** to get started.")
