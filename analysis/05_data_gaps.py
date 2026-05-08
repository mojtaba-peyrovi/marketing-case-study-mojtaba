"""
Q5: Data Gaps & Additional Inputs

Identifies what data is missing from the current dataset and what would materially
improve the analysis quality and decision-making confidence.

Methodology:
- Quantify existing null/missing values
- Identify structural gaps (columns that don't exist but would be analytically valuable)
- Map each gap to its business impact and a practical data source

Output: output/data/data_gaps.json
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

OUTPUT_DATA = os.path.join(os.path.dirname(__file__), "..", "output", "data")


def run(df_full, df_conv):
    os.makedirs(OUTPUT_DATA, exist_ok=True)

    # ── Quantify existing null data ───────────────────────────────────────────
    total_rows = len(df_full)
    null_counts = df_full.isnull().sum()
    null_summary = [
        {
            "column": col,
            "null_count": int(null_counts[col]),
            "null_pct": round(null_counts[col] / total_rows * 100, 1),
        }
        for col in null_counts.index
        if null_counts[col] > 0
    ]

    # ── UNKNOWN category counts ───────────────────────────────────────────────
    unknown_market = int((df_full["Market"] == "UNKNOWN").sum())
    unknown_ch1 = int((df_full["Conversion Channel 1"] == "UNKNOWN").sum())
    unknown_ch3 = int((df_full["Conversion Channel 3"].str.strip() == "UNKNOWN").sum())

    # ── Structural data gaps ──────────────────────────────────────────────────
    gaps = [
        {
            "gap": "No Customer Lifetime Value (LTV) data",
            "impact": "Cannot calculate LTV:CAC ratio — the gold-standard metric for sustainable growth. Without LTV, budget decisions are based on acquisition cost alone, ignoring long-term value.",
            "suggested_data_source": "Subscription platform data: link subscriber IDs to renewal history, average subscription tenure, and total revenue per customer.",
            "priority": "Critical",
        },
        {
            "gap": "No churn / retention rate by channel",
            "impact": "A channel may have a low CAC but if it acquires churners, it destroys value. Without churn data by acquisition channel, we cannot identify which channels acquire loyal subscribers.",
            "suggested_data_source": "Subscription management system (e.g. Stripe, RevenueCat): pull cohort retention by acquisition source.",
            "priority": "Critical",
        },
        {
            "gap": "Conversion data missing for 62% of rows (718/1,152)",
            "impact": "Monthly Conversions, Yearly Conversions, and Revenue columns are null for the majority of channel-month combinations. This limits conversion rate and revenue analysis to only the tracked subset.",
            "suggested_data_source": "Expand conversion tracking to all channel combinations — especially organic and non-paid channels which currently lack conversion attribution.",
            "priority": "High",
        },
        {
            "gap": "No creative-level or campaign-level breakdown",
            "impact": "Budget decisions are made at Channel 3 granularity (e.g. 'Facebook/Instagram Ads') but cannot be attributed to specific ad creatives, copy variations, or audience segments.",
            "suggested_data_source": "Facebook Ads Manager / Google Ads API: pull campaign, ad set, and ad-level performance data.",
            "priority": "High",
        },
        {
            "gap": "No demographic or psychographic data on converters",
            "impact": "the Company's target audience is 20–35y, mostly female. Without demographic data, we cannot verify whether campaigns are reaching the intended audience or acquiring off-target users.",
            "suggested_data_source": "Platform signup data (age, gender, location), Facebook Ads audience insights, or an onboarding survey.",
            "priority": "High",
        },
        {
            "gap": "UNKNOWN market rows (288 rows, 25% of dataset)",
            "impact": "One quarter of all rows cannot be attributed to a language audience. This prevents accurate per-audience budget allocation and ROAS analysis.",
            "suggested_data_source": "Improve UTM tagging and attribution logic in the marketing stack. Audit the pipeline that assigns market labels.",
            "priority": "High",
        },
        {
            "gap": "No A/B test or experiment identifiers",
            "impact": "Cannot distinguish organic performance changes from the effect of deliberate experiments. Any trend may be confounded by concurrent tests.",
            "suggested_data_source": "Experiment management tool (e.g. LaunchDarkly, Optimizely, or internal feature flags): join experiment IDs to conversion data.",
            "priority": "Medium",
        },
        {
            "gap": "No content performance data (which audios drive subscriptions)",
            "impact": "the Company is an audio-first product. Without knowing which content titles or categories drive trial starts, content investment decisions are decoupled from acquisition performance.",
            "suggested_data_source": "Product analytics (Amplitude, Mixpanel): track first-listen -> trial start -> conversion funnels per audio title.",
            "priority": "Medium",
        },
        {
            "gap": "Only one year of data (2024)",
            "impact": "Cannot assess YoY growth, seasonality baselines, or long-term channel trends. A single year could represent an anomalous period.",
            "suggested_data_source": "Historical data from 2022–2023 using the same schema to enable trend analysis and seasonal decomposition.",
            "priority": "Medium",
        },
        {
            "gap": "No impression or reach data for non-paid channels",
            "impact": "Cannot calculate organic conversion rates (impressions -> trials). Without reach data, we cannot assess the efficiency of owned channels like IG Channel, YT Channel, or Newsletter.",
            "suggested_data_source": "Social media analytics APIs (Instagram, YouTube, Spotify for Podcasters): pull monthly impressions, reach, and click-through rates.",
            "priority": "Medium",
        },
    ]

    result = {
        "dataset_overview": {
            "total_rows": total_rows,
            "null_value_summary": null_summary,
            "unknown_category_counts": {
                "unknown_market_rows": unknown_market,
                "unknown_channel1_rows": unknown_ch1,
                "unknown_channel3_rows": unknown_ch3,
            },
        },
        "data_gaps": gaps,
    }

    out_path = os.path.join(OUTPUT_DATA, "data_gaps.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  [Q5] Data gaps saved -> {out_path}")
    return result

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_loader import load_data
    df_full, df_conv = load_data()
    run(df_full, df_conv)
