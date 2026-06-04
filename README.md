# WP-06: Operations Dashboard

## Overview

A non-technical, self-serve operations dashboard built with Streamlit for EasySkill Career Academy. It provides counselors and management with real-time visibility into pipeline health, with all metrics mathematically reconciling with the WP-05 analytics module.

## Features

* **Interactive Global Filters:** Slice data dynamically by Date Range and Lead Source.
* **Top-Level KPI Cards:** Instant tracking of Total Leads, Conversion Rate, and Active Leads.
* **Dynamic Funnel Chart:** Visualizes conversion drop-off across the official pipeline stages (New → Contacted → Qualified → Demo → Enrolled).
* **Recent Leads Table:** A clean, scrollable view of the most recent pipeline additions.

## Prerequisites

* Python 3.x
* The WP-03 Flask API must be running locally to serve data to the dashboard.

## Installation

Ensure your virtual environment is active, then install the front-end dependencies:

```bash
pip install streamlit pandas requests plotly

```

## Usage

### Option 1: Unified Runner (Recommended)

To launch both the backend Flask API and the frontend Streamlit dashboard simultaneously using the central process manager:

```bash
python main.py

```

### Option 2: Standalone Execution

If your Flask API is already running in a separate terminal, launch the dashboard directly:

```bash
streamlit run src/dashboard/app.py

```

The dashboard will automatically open in your default web browser at `http://localhost:8501`.