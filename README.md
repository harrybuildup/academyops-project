# AcademyOps — WP-05: Funnel Analytics & Statistical Reporting

## 📌 Overview

This module transitions AcademyOps from backend data engineering to **Data Science & Business Intelligence**. The objective is to extract raw CRM lead data and compute stage-by-stage pipeline conversion rates, time-in-stage averages, and lead source performance to provide actionable insights for Leadership and Marketing.

## 🛠 Tech Stack

* **Language:** Python 3.x
* **Environment:** Jupyter Notebooks (`.ipynb`) via VS Code
* **Data Handling:** `pandas`, `sqlite3`
* **Statistical Testing:** `scipy`, `statsmodels`
* **Visualization:** `plotly`

## 📂 Project Structure

```text
academyops/
│
├── data/
│   └── academyops.db         # Read-only SQLite database (Generated in WP-01/02)
│
└── notebooks/
    ├── analytics.ipynb       # Core data science notebook and visualizations
    └── README.md             # This file

```

## 🚀 Setup & Execution

1. **Activate your virtual environment** (from the project root):
```bash
# Mac/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

```


2. **Install necessary data science dependencies**:
```bash
pip install pandas scipy statsmodels plotly ipykernel

```


3. **Run the Notebook**:
* Open `notebooks/analytics.ipynb` in VS Code or your preferred Jupyter environment.
* Execute the cells sequentially from top to bottom.



## 📊 Core Features & Logic

* **Cumulative Funnel Engineering:** Because the legacy database strictly stores "snapshot" state data (overwriting previous stages), this module dynamically rebuilds a linear historical funnel using cumulative counts to calculate accurate stage-to-stage conversion rates (New → Contacted → Qualified → Demo → Enrolled).
* **Time-in-Stage Proxy:** Utilizes `created_at` and `updated_at` timestamps to compute the average number of days it takes for a lead to reach their current pipeline stage.
* **Hypothesis Testing:** Replaces anecdotal marketing assumptions with formal statistics. Automates a **Two-Proportion Z-Test** (Alpha = 0.05) to mathematically evaluate if the conversion rate variance between the top two lead sources is statistically significant or merely due to random chance.
* **Interactive Visualizations:** Generates embedded, interactive `plotly` Funnel Charts and Source-Comparison Bar Charts.

## 📝 Final Findings

The final deliverable includes a plain-language Executive Summary (located at the bottom of the notebook) detailing drop-off bottlenecks and a formal conclusion regarding lead source budget allocation based on the generated p-value.