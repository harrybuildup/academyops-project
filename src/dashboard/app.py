"""src/dashboard/app.py — AcademyOps Operations Dashboard (Streamlit).

Fetches data from the FastAPI backend at http://localhost:8000.
Start with:  streamlit run src/dashboard/app.py
"""

import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="AcademyOps Dashboard", layout="wide")


@st.cache_data(ttl=60)
def fetch_all_leads() -> pd.DataFrame:
    """Fetch every lead from the API, walking through pages."""
    leads = []
    page, limit = 1, 100

    try:
        while True:
            r = requests.get(f"{API_BASE}/leads", params={"page": page, "limit": limit}, timeout=10)
            r.raise_for_status()
            body = r.json()
            batch = body.get("data", [])
            if not batch:
                break
            leads.extend(batch)
            if len(batch) < limit:
                break
            page += 1

        if not leads:
            return pd.DataFrame()

        df = pd.DataFrame(leads)
        for col in ("created_at", "updated_at"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the API. Is it running on http://localhost:8000?")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to fetch leads: {e}")
        return pd.DataFrame()


# ── Load data ──────────────────────────────────────────────────────────────

df_raw = fetch_all_leads()

st.title("AcademyOps Operations Dashboard")

if df_raw.empty:
    st.warning("No leads found. Make sure the API is running and the database is seeded.")
    st.stop()

# ── Sidebar filters ────────────────────────────────────────────────────────

st.sidebar.header("Filters")

sources = ["All"] + sorted(df_raw["source"].dropna().unique().tolist())
selected_source = st.sidebar.selectbox("Lead Source", sources)

min_date = df_raw["created_at"].min().date()
max_date = df_raw["created_at"].max().date()
date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)

# ── Apply filters ──────────────────────────────────────────────────────────

df = df_raw.copy()
if selected_source != "All":
    df = df[df["source"] == selected_source]
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
    df = df[(df["created_at"] >= start) & (df["created_at"] < end)]

# ── KPI cards ──────────────────────────────────────────────────────────────

st.markdown("### Pipeline Overview")
total = len(df)
enrolled = len(df[df["stage"] == "Enrolled"])
conversion = (enrolled / total * 100) if total else 0
active = len(df[~df["stage"].isin(["Enrolled", "Lost"])])

c1, c2, c3 = st.columns(3)
c1.metric("Total Leads", total)
c2.metric("Conversion Rate", f"{conversion:.1f}%")
c3.metric("Active Leads", active)

st.markdown("---")

# ── Funnel chart ───────────────────────────────────────────────────────────

st.markdown("### Conversion Funnel")
stage_order = ["New", "Contacted", "Qualified", "Demo", "Enrolled"]
counts = df["stage"].value_counts().reindex(stage_order).fillna(0).reset_index()
counts.columns = ["Stage", "Count"]
st.plotly_chart(
    px.funnel(counts, x="Count", y="Stage", color_discrete_sequence=["#4C78A8"]),
    use_container_width=True,
)

st.markdown("---")

# ── Recent leads table ─────────────────────────────────────────────────────

st.markdown("### Recent Leads")
if df.empty:
    st.info("No leads match the current filters.")
else:
    recent = df.sort_values("created_at", ascending=False).head(10).copy()
    recent["created_at"] = recent["created_at"].dt.strftime("%Y-%m-%d %H:%M")
    show_cols = [c for c in ["id", "name", "phone", "stage", "source", "created_at"] if c in recent.columns]
    st.dataframe(recent[show_cols], use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Download filtered leads as CSV",
        data=df.to_csv(index=False),
        file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# ── Debug ──────────────────────────────────────────────────────────────────

with st.expander("🔧 Debug info"):
    st.write(f"Total fetched: {len(df_raw)} | After filters: {len(df)}")
    st.write(f"Source: {selected_source} | Date range: {date_range}")
