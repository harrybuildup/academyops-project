import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:5000/api/v1"
st.set_page_config(page_title="AcademyOps Dashboard", layout="wide")

@st.cache_data(ttl=60)
def fetch_all_leads():
    """
    Fetches ALL leads from the API, handling pagination.
    """
    all_leads = []
    page = 1
    page_size = 100  # Fetch 100 at a time
    
    try:
        while True:
            # Request page with large limit
            response = requests.get(
                f"{API_BASE_URL}/leads",
                params={
                    "page": page,
                    "limit": page_size
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different API response formats
            leads = data.get('data', []) if isinstance(data, dict) else data
            
            if not leads:
                break  # No more pages
            
            all_leads.extend(leads)
            page += 1
            
            # Safety check: stop if we get less than a full page
            if len(leads) < page_size:
                break
        
        # Convert to DataFrame
        if all_leads:
            df = pd.DataFrame(all_leads)
            
            # Ensure dates are properly formatted
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
                
            return df
        else:
            return pd.DataFrame()
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Is it running on http://127.0.0.1:5000?")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to fetch leads: {e}")
        return pd.DataFrame()


# Load all data
df_raw = fetch_all_leads()

# --- Main Content ---
st.title("AcademyOps Operations Dashboard")

if df_raw.empty:
    st.warning("⚠️ No leads found. Check your API connection or database.")
    st.info("Expected API running at: http://127.0.0.1:5000")
else:
    st.write(f"📊 **Total leads in database: {len(df_raw)}**")
    
    # --- Sidebar Filters ---
    st.sidebar.header("Global Filters")
    
    # 1. Source Filter
    unique_sources = ["All"] + sorted(df_raw['source'].dropna().unique().tolist())
    selected_source = st.sidebar.selectbox("Lead Source", unique_sources)
    
    # 2. Date Range Filter
    min_date = df_raw['created_at'].min().date()
    max_date = df_raw['created_at'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # --- Apply Filters ---
    df_filtered = df_raw.copy()
    
    # Filter by source
    if selected_source != "All":
        df_filtered = df_filtered[df_filtered['source'] == selected_source]
    
    # Filter by date range
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        
        df_filtered = df_filtered[
            (df_filtered['created_at'] >= start_dt) &
            (df_filtered['created_at'] < end_dt)
        ]
    
    # --- Display Results ---
    st.subheader(f"Leads Displayed: {len(df_filtered)} / {len(df_raw)}")
    
    if not df_filtered.empty:
        # Reorder columns for better readability
        cols_to_show = ['created_at', 'id', 'name', 'phone', 'source', 'stage', 'notes', 'updated_at']
        cols_to_show = [c for c in cols_to_show if c in df_filtered.columns]
        
        # Display table
        st.dataframe(
            df_filtered[cols_to_show],
            use_container_width=True,
            hide_index=True
        )
        
        # Download CSV option
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No leads match your filters.")

    if not df_filtered.empty:
        
        # --- 1. KPI Cards (FR-1) ---
        st.markdown("### Pipeline Overview")
        
        # Calculate Metrics
        total_leads = len(df_filtered)
        enrolled_leads = len(df_filtered[df_filtered['stage'] == 'Enrolled'])
        conversion_rate = (enrolled_leads / total_leads * 100) if total_leads > 0 else 0
        active_leads = len(df_filtered[~df_filtered['stage'].isin(['Enrolled', 'Dropped'])])

        # Display Metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Leads", total_leads)
        col2.metric("Conversion Rate", f"{conversion_rate:.1f}%")
        col3.metric("Active Leads", active_leads)

        st.markdown("---")

        # --- 2. Funnel Chart (FR-3) ---
        st.markdown("### Conversion Funnel")
        
        # Define the exact order of stages we expect
        stage_order = ['New', 'Contacted', 'Qualified', 'Demo', 'Enrolled']
        
        # Count leads per stage based on the filtered data
        stage_counts = df_filtered['stage'].value_counts().reindex(stage_order).fillna(0).reset_index()
        stage_counts.columns = ['Stage', 'Count']
        
        # Create the Plotly Funnel Chart
        fig_funnel = px.funnel(
            stage_counts, 
            x='Count', 
            y='Stage',
            color_discrete_sequence=['#4C78A8'] # A nice professional blue
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

        st.markdown("---")

        # --- 3. Recent Leads Table (FR-4) ---
        st.markdown("### Recent Leads")
        
        # Sort by creation date descending and take the top 10
        recent_leads = df_filtered.sort_values(by='created_at', ascending=False).head(10)
        
        # Select specific columns to display to keep the UI clean
        display_columns = ['id', 'name', 'phone', 'stage', 'source', 'created_at']
        # Format the date to look cleaner
        recent_leads['created_at'] = recent_leads['created_at'].dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            recent_leads[display_columns],
            use_container_width=True,
            hide_index=True
        )

    else:
        # Friendly empty state (Testing Checklist requirement)
        st.info("No leads match the current filter criteria. Try expanding your date range or changing the source.")

    
    
    # --- Debug Info (collapsible) ---
    with st.expander("🔧 Debug Info"):
        st.write(f"Total records fetched: {len(df_raw)}")
        st.write(f"Records after filtering: {len(df_filtered)}")
        st.write(f"Date range filter: {date_range if len(date_range) == 2 else 'Not set'}")
        st.write(f"Source filter: {selected_source}")
        st.write("\n**Sample of raw data:**")
        st.dataframe(df_raw.head(5))