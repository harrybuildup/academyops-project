"""scripts/analytics.py — WP-05 Funnel Analytics & Statistical Reporting.

Computes funnel conversion rates, average time-in-stage, and source
performance, then runs a hypothesis test comparing conversion across two
sources and prints a plain-language conclusion.

Charts are saved to data/charts/ as PNG files.

Usage
-----
    python scripts/analytics.py
    python scripts/analytics.py --source1 Google --source2 Facebook
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_leads() -> pd.DataFrame:
    """Pull all leads from the database into a DataFrame."""
    from src.database.connections import get_session_factory
    import src.models.lead  # noqa: F401 — register ORM
    from src.models.lead import LeadORM

    db = get_session_factory()()
    try:
        rows = db.query(LeadORM).all()
        if not rows:
            print("No leads in database. Run 'python scripts/seed_db.py' first.")
            sys.exit(0)

        data = [
            {
                "id":         r.id,
                "name":       r.name,
                "source":     r.source or "Unknown",
                "stage":      r.stage,
                "notes":      r.notes,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in rows
        ]
    finally:
        db.close()

    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    df["days_in_stage"] = (df["updated_at"] - df["created_at"]).dt.total_seconds() / 86400
    return df


# ---------------------------------------------------------------------------
# Funnel metrics
# ---------------------------------------------------------------------------

STAGE_ORDER = ["New", "Contacted", "Qualified", "Demo", "Enrolled"]


def funnel_counts(df: pd.DataFrame) -> pd.Series:
    """Count leads at each pipeline stage (non-Lost only, ordered)."""
    counts = df[df["stage"] != "Lost"]["stage"].value_counts()
    return counts.reindex(STAGE_ORDER).fillna(0).astype(int)


def conversion_rates(counts: pd.Series) -> list[tuple[str, str, float]]:
    """Return stage-to-stage conversion rates as (from, to, pct) tuples."""
    rates = []
    values = counts.values
    for i in range(len(STAGE_ORDER) - 1):
        from_stage = STAGE_ORDER[i]
        to_stage   = STAGE_ORDER[i + 1]
        from_count = values[i]
        to_count   = values[i + 1]
        rate = (to_count / from_count * 100) if from_count > 0 else 0.0
        rates.append((from_stage, to_stage, round(rate, 1)))
    return rates


def avg_time_in_stage(df: pd.DataFrame) -> pd.Series:
    """Mean days between created_at and updated_at per stage."""
    return (
        df.groupby("stage")["days_in_stage"]
        .mean()
        .reindex(STAGE_ORDER + ["Lost"])
        .fillna(0)
        .round(1)
    )


# ---------------------------------------------------------------------------
# Source performance
# ---------------------------------------------------------------------------

def source_conversion(df: pd.DataFrame) -> pd.DataFrame:
    """Conversion rate (% Enrolled) per source."""
    total    = df.groupby("source").size().rename("total")
    enrolled = df[df["stage"] == "Enrolled"].groupby("source").size().rename("enrolled")
    src_df = pd.concat([total, enrolled], axis=1).fillna(0).astype({"total": int, "enrolled": int})
    src_df["conversion_pct"] = (src_df["enrolled"] / src_df["total"] * 100).round(1)
    return src_df.sort_values("conversion_pct", ascending=False)


# ---------------------------------------------------------------------------
# Hypothesis test
# ---------------------------------------------------------------------------

def two_proportion_z_test(
    df: pd.DataFrame,
    source1: str,
    source2: str,
    alpha: float = 0.05,
) -> dict:
    """Two-proportion z-test comparing enrollment rates for source1 vs source2."""
    def counts(src: str) -> tuple[int, int]:
        sub = df[df["source"] == src]
        n = len(sub)
        k = len(sub[sub["stage"] == "Enrolled"])
        return k, n

    k1, n1 = counts(source1)
    k2, n2 = counts(source2)

    if n1 == 0 or n2 == 0:
        return {
            "source1": source1, "source2": source2,
            "error": "One or both sources have no leads.",
        }

    p1 = k1 / n1
    p2 = k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se if se > 0 else 0.0
    p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z)))
    significant = p_value < alpha

    conclusion = (
        f"There IS a statistically significant difference in enrollment rate "
        f"between {source1} ({p1*100:.1f}%) and {source2} ({p2*100:.1f}%) "
        f"(z={z:.2f}, p={p_value:.4f} < α={alpha})."
        if significant else
        f"There is NO statistically significant difference in enrollment rate "
        f"between {source1} ({p1*100:.1f}%) and {source2} ({p2*100:.1f}%) "
        f"(z={z:.2f}, p={p_value:.4f} ≥ α={alpha})."
    )

    return {
        "source1": source1, "n1": n1, "enrolled1": k1, "rate1_pct": round(p1 * 100, 1),
        "source2": source2, "n2": n2, "enrolled2": k2, "rate2_pct": round(p2 * 100, 1),
        "z_statistic": round(z, 4),
        "p_value": round(p_value, 4),
        "alpha": alpha,
        "significant": significant,
        "conclusion": conclusion,
    }


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def save_funnel_chart(counts: pd.Series, out_path: str) -> None:
    stages = [s for s in STAGE_ORDER if counts.get(s, 0) > 0 or s in counts.index]
    values = [counts.get(s, 0) for s in stages]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4C78A8", "#72B7B2", "#54A24B", "#EECA3B", "#E45756"]
    bars = ax.barh(stages[::-1], values[::-1], color=colors[:len(stages)][::-1])
    ax.set_xlabel("Number of Leads")
    ax.set_title("AcademyOps Sales Funnel")
    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                str(int(val)), va="center", fontsize=10)
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"  Saved: {out_path}")


def save_source_chart(src_df: pd.DataFrame, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    src_df["conversion_pct"].plot(kind="bar", ax=ax, color="#4C78A8", edgecolor="white")
    ax.set_title("Enrollment Conversion Rate by Lead Source")
    ax.set_ylabel("Conversion Rate (%)")
    ax.set_xlabel("Source")
    ax.set_xticklabels(src_df.index, rotation=30, ha="right")
    for i, v in enumerate(src_df["conversion_pct"]):
        ax.text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=9)
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"  Saved: {out_path}")


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------

def run(source1: str = "Google", source2: str = "Facebook") -> None:
    print("\n══════════════════════════════════════════════════════")
    print("  AcademyOps — Funnel Analytics & Statistical Report")
    print("══════════════════════════════════════════════════════\n")

    df = load_leads()
    print(f"Total leads loaded: {len(df)}\n")

    # ── Funnel ──────────────────────────────────────────────────────────────
    counts = funnel_counts(df)
    rates  = conversion_rates(counts)

    print("── Stage Counts ───────────────────────────────────────")
    for stage in STAGE_ORDER:
        print(f"  {stage:<12} {counts[stage]:>4}")
    lost = len(df[df["stage"] == "Lost"])
    print(f"  {'Lost':<12} {lost:>4}")

    print("\n── Stage-to-Stage Conversion ──────────────────────────")
    for from_s, to_s, pct in rates:
        print(f"  {from_s} → {to_s}: {pct}%")

    overall = (counts["Enrolled"] / counts["New"] * 100) if counts["New"] > 0 else 0
    print(f"\n  Overall (New → Enrolled): {overall:.1f}%")

    # ── Time in stage ────────────────────────────────────────────────────────
    avg_days = avg_time_in_stage(df)
    print("\n── Average Time in Stage (days) ───────────────────────")
    for stage in STAGE_ORDER + ["Lost"]:
        print(f"  {stage:<12} {avg_days[stage]:>6.1f} days")

    # ── Source performance ───────────────────────────────────────────────────
    src_df = source_conversion(df)
    print("\n── Conversion Rate by Source ──────────────────────────")
    print(f"  {'Source':<14} {'Total':>6} {'Enrolled':>9} {'Rate':>8}")
    print("  " + "─" * 42)
    for src, row in src_df.iterrows():
        print(f"  {src:<14} {int(row.total):>6} {int(row.enrolled):>9} {row.conversion_pct:>7.1f}%")

    # ── Hypothesis test ──────────────────────────────────────────────────────
    print(f"\n── Hypothesis Test: {source1} vs {source2} ──────────────────")
    result = two_proportion_z_test(df, source1, source2)
    if "error" in result:
        print(f"  ⚠  {result['error']}")
    else:
        print(f"  Test        : Two-proportion z-test")
        print(f"  α (alpha)   : {result['alpha']}")
        print(f"  {source1:<12}: {result['n1']} leads, {result['enrolled1']} enrolled ({result['rate1_pct']}%)")
        print(f"  {source2:<12}: {result['n2']} leads, {result['enrolled2']} enrolled ({result['rate2_pct']}%)")
        print(f"  z-statistic : {result['z_statistic']}")
        print(f"  p-value     : {result['p_value']}")
        print(f"  Significant : {'Yes' if result['significant'] else 'No'}")
        print(f"\n  Conclusion  : {result['conclusion']}")

    # ── Charts ───────────────────────────────────────────────────────────────
    print("\n── Generating Charts ──────────────────────────────────")
    save_funnel_chart(counts, "data/charts/funnel.png")
    save_source_chart(src_df, "data/charts/source_conversion.png")

    print("\n✅  Report complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run funnel analytics report.")
    parser.add_argument("--source1", default="Google",   help="First source for hypothesis test")
    parser.add_argument("--source2", default="Facebook", help="Second source for hypothesis test")
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    run(source1=args.source1, source2=args.source2)
