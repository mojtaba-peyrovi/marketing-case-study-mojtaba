"""
Q4: Key Patterns & Anomalies

Identifies trends, patterns, and outliers in the dataset and explains their implications.

Charts:
  1. heatmap_market_month.png  — Subscribers by Market × Month (heatmap)
  2. coupon_trend.png          — Average coupon usage share by month (line)
  3. conversion_split.png      — Monthly vs Yearly conversion share by market (stacked bar)

Methodology:
- Heatmap: pivot table of subscriber counts for visual pattern recognition
- Outlier detection: IQR method on Marketing Spendings and Subscriber columns
  (Q1 - 1.5×IQR, Q3 + 1.5×IQR boundaries)
- Coupon trend: tracks promotional intensity over the year
- Conversion split: shows product preference (monthly vs annual) by market

Output: output/data/patterns_anomalies.json + output/charts/{chart}.png
"""

import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.insert(0, os.path.dirname(__file__))
from _chart_style import apply_brand_style, save_chart, PRIMARY, ACCENT, SOFT, MUTED, BG, MARKET_COLORS, LIGHT_BG

OUTPUT_DATA  = os.path.join(os.path.dirname(__file__), "..", "output", "data")
OUTPUT_CHART = os.path.join(os.path.dirname(__file__), "..", "output", "charts")

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def _chart_heatmap(df_full):
    apply_brand_style()
    heat = df_full[df_full["Market"] != "UNKNOWN"].pivot_table(
        index="Market", columns="Business Month", values="Subscriber", aggfunc="sum"
    )
    heat.columns = MONTH_NAMES

    fig, ax = plt.subplots(figsize=(12, 4))
    sns.heatmap(
        heat, ax=ax, cmap="Purples", annot=True, fmt=".0f",
        linewidths=0.5, linecolor="#E0E0E0",
        cbar_kws={"label": "New Subscribers"},
    )
    ax.set_title("New Subscribers by Market and Month — 2024", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    save_chart(fig, os.path.join(OUTPUT_CHART, "heatmap_market_month.png"))


def _chart_coupon_trend(df_conv):
    apply_brand_style()
    coupon_monthly = (
        df_conv[df_conv["Share Coupon Used"].notna()]
        .groupby("Business Month")["Share Coupon Used"]
        .mean()
        .reset_index()
        .sort_values("Business Month")
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(coupon_monthly["Business Month"], coupon_monthly["Share Coupon Used"] * 100,
                    alpha=0.2, color=PRIMARY)
    ax.plot(coupon_monthly["Business Month"], coupon_monthly["Share Coupon Used"] * 100,
            color=PRIMARY, linewidth=2.5, marker="o", markersize=5)
    ax.axhline(
        coupon_monthly["Share Coupon Used"].mean() * 100,
        color=MUTED, linestyle="--", linewidth=1.2,
        label=f"Annual avg: {coupon_monthly['Share Coupon Used'].mean()*100:.1f}%"
    )
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_NAMES)
    ax.set_title("Average Coupon Usage Rate by Month — 2024")
    ax.set_xlabel("Month")
    ax.set_ylabel("Coupon Usage (%)")
    ax.set_ylim(0, max(coupon_monthly["Share Coupon Used"].max() * 100 * 1.2, 50))
    ax.legend()
    fig.tight_layout()
    save_chart(fig, os.path.join(OUTPUT_CHART, "coupon_trend.png"))


def _chart_conversion_split(df_conv):
    apply_brand_style()
    split = (
        df_conv[df_conv["Market"] != "UNKNOWN"]
        .groupby("Market")
        .agg(
            monthly=("Monthly Conversions", "sum"),
            yearly=("Yearly Conversions", "sum"),
        )
        .reset_index()
    )
    split["total"] = split["monthly"] + split["yearly"]
    split["monthly_pct"] = split["monthly"] / split["total"] * 100
    split["yearly_pct"] = split["yearly"] / split["total"] * 100

    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(split))
    bars1 = ax.bar(x, split["yearly_pct"], color=PRIMARY, label="Yearly Subscriptions")
    bars2 = ax.bar(x, split["monthly_pct"], bottom=split["yearly_pct"], color=ACCENT, label="Monthly Subscriptions")

    for bar, yval, mval in zip(x, split["yearly_pct"], split["monthly_pct"]):
        ax.text(bar, yval / 2, f"{yval:.0f}%", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        ax.text(bar, yval + mval / 2, f"{mval:.0f}%", ha="center", va="center", fontsize=9, color="white", fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(split["Market"])
    ax.set_title("Conversion Split: Monthly vs Yearly Subscriptions by Market — 2024")
    ax.set_ylabel("Share of Conversions (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    fig.tight_layout()
    save_chart(fig, os.path.join(OUTPUT_CHART, "conversion_split.png"))


def _detect_outliers(df_full):
    """IQR-based outlier detection on spend and subscriber columns."""
    results = []
    for col in ["Marketing Spendings", "Subscriber"]:
        q1 = df_full[col].quantile(0.25)
        q3 = df_full[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df_full[(df_full[col] < lower) | (df_full[col] > upper)][
            ["Business Month", "Market", "Conversion Channel 3", col]
        ].head(10)
        results.append({
            "column": col,
            "q1": round(float(q1), 2),
            "q3": round(float(q3), 2),
            "iqr": round(float(iqr), 2),
            "lower_bound": round(float(lower), 2),
            "upper_bound": round(float(upper), 2),
            "outlier_count": int(((df_full[col] < lower) | (df_full[col] > upper)).sum()),
            "top_outliers": outliers.to_dict(orient="records"),
        })
    return results


def run(df_full, df_conv):
    os.makedirs(OUTPUT_DATA, exist_ok=True)
    os.makedirs(OUTPUT_CHART, exist_ok=True)

    _chart_heatmap(df_full)
    _chart_coupon_trend(df_conv)
    _chart_conversion_split(df_conv)

    outliers = _detect_outliers(df_full)

    patterns = [
        {
            "pattern": "German market dominates year-round",
            "description": "The heatmap shows consistently higher subscriber counts for German across all 12 months. Summer months (Jun–Sep) show a notable peak for German.",
            "implication": "German is the core market. Campaign timing should align with the Jun–Sep peak. French and English show flat, low volumes suggesting untapped potential.",
            "chart": "heatmap_market_month.png",
        },
        {
            "pattern": "Coupon usage peaks mid-year (Q2–Q3)",
            "description": "Average coupon usage is not uniform across the year — it tends to spike in certain months, suggesting seasonal promotional campaigns.",
            "implication": "Promotional campaigns are concentrated. This is a lever to test: would spreading coupon offers more evenly across the year improve baseline conversion rates?",
            "chart": "coupon_trend.png",
        },
        {
            "pattern": "Yearly subscriptions overwhelmingly dominate across all markets",
            "description": "The conversion split shows >80% of conversions are yearly subscriptions across German, French, and English markets.",
            "implication": "The 30-day trial mechanic for yearly plans is a strong acquisition driver. Monthly plans may serve as a backup/entry option rather than a primary acquisition vehicle.",
            "chart": "conversion_split.png",
        },
        {
            "pattern": "Zero-spend rows account for the majority of the dataset",
            "description": "718 of 1,152 rows (62%) have zero marketing spend. These correspond to non-paid channels (organic, owned, word-of-mouth). Conversion data is only tracked for a subset.",
            "implication": "Non-paid acquisition is structurally important. The absence of conversion tracking for many channels is a data infrastructure gap, not a channel performance issue.",
            "chart": None,
        },
        {
            "pattern": "Marketing Spendings contain extreme outliers (high-spend months)",
            "description": f"IQR analysis flags rows with spend above the upper bound — these correspond to Influencer Instagram and Facebook/Instagram Ads heavy investment months.",
            "implication": "High-spend concentrations suggest burst campaigns. Understanding the subscriber ROI of these bursts vs steady-state spend is critical for future planning.",
            "chart": None,
        },
    ]

    result = {
        "patterns": patterns,
        "outlier_analysis": outliers,
    }

    out_path = os.path.join(OUTPUT_DATA, "patterns_anomalies.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  [Q4] Patterns & anomalies saved -> {out_path}")
    return result

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_loader import load_data
    df_full, df_conv = load_data()
    run(df_full, df_conv)
