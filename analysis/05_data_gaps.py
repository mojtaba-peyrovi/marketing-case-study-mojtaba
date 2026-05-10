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


def _spend_tracking_integrity(df_full):
    """
    Investigates the 434 rows where Conversion Channel 1 = 'Paid' but
    Marketing Spendings = 0. Splits them into:
      A) placeholder rows (zero everything — every market/month/channel scaffold)
      B) live rows with conversions/revenue but no spend booked — the integrity issue.

    Returns a dict with:
      - headline numbers
      - per-market summary (untracked-revenue %)
      - per-(market, channel) breakdown of how many active months are missing spend
    """
    df = df_full.copy()
    paid_zero = (df["Conversion Channel 1"] == "Paid") & (df["Marketing Spendings"] == 0)

    # A) placeholder rows: 0 spend, 0 subs, 0 conv, 0 rev
    has_activity = (
        (df["Subscriber"].fillna(0) > 0) |
        (df["Monthly Conversions"].fillna(0) > 0) |
        (df["Yearly Conversions"].fillna(0) > 0) |
        (df["New Revenue Invoice Date"].fillna(0) > 0)
    )
    placeholder_rows = int((paid_zero & ~has_activity).sum())
    integrity_rows = int((paid_zero & has_activity).sum())

    # Per-market summary (known markets only)
    known = df[df["Market"].isin(["English", "French", "German"])]
    market_summary = []
    for m in ["English", "French", "German"]:
        md = known[known["Market"] == m]
        rev = float(md["New Revenue Invoice Date"].fillna(0).sum())
        spend = float(md["Marketing Spendings"].sum())
        rev_no_spend = float(
            md.loc[md["Marketing Spendings"] == 0, "New Revenue Invoice Date"].fillna(0).sum()
        )
        market_summary.append({
            "market": m,
            "total_revenue": int(rev),
            "total_spend": int(spend),
            "revenue_with_no_spend": int(rev_no_spend),
            "pct_revenue_untracked": round(rev_no_spend / rev * 100, 1) if rev else None,
            "reported_roas": round(rev / spend, 2) if spend else None,
        })

    # Per (market, channel) breakdown — only Paid rows that had real activity
    paid_active = known[(known["Conversion Channel 1"] == "Paid") & has_activity.loc[known.index]]
    g = (
        paid_active
        .groupby(["Market", "Conversion Channel 3"])
        .agg(
            months_with_activity=("Marketing Spendings", "size"),
            months_with_spend=("Marketing Spendings", lambda s: int((s > 0).sum())),
            revenue=("New Revenue Invoice Date", lambda s: int(s.fillna(0).sum())),
            spend=("Marketing Spendings", lambda s: int(s.sum())),
        )
        .reset_index()
    )
    g["months_missing_spend"] = g["months_with_activity"] - g["months_with_spend"]
    g = g[g["months_missing_spend"] > 0].sort_values(
        ["Market", "months_missing_spend"], ascending=[True, False]
    )
    channel_breakdown = [
        {
            "market": r["Market"],
            "channel": r["Conversion Channel 3"],
            "months_with_activity": int(r["months_with_activity"]),
            "months_with_spend": int(r["months_with_spend"]),
            "months_missing_spend": int(r["months_missing_spend"]),
            "revenue": int(r["revenue"]),
            "spend": int(r["spend"]),
        }
        for _, r in g.iterrows()
    ]

    return {
        "placeholder_rows": placeholder_rows,
        "integrity_rows": integrity_rows,
        "market_summary": market_summary,
        "channel_breakdown": channel_breakdown,
    }


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

    # ── Spend tracking integrity (the 0-spend Paid rows finding) ─────────────
    spend_tracking = _spend_tracking_integrity(df_full)

    # ── Structural data gaps ──────────────────────────────────────────────────
    gaps = [
        {
            "gap": "Spend-tracking gap: 64% of English-market revenue has no spend recorded",
            "impact": "Across 119 active rows, conversions and revenue are booked against Paid channels (Google, TikTok, IG-Influencer, Podcast) with zero matching spend. The English market is hit hardest — its reported ROAS and CAC are unreliable and cannot be compared against German/French until fixed.",
            "suggested_data_source": "Audit the marketing-spend ETL: confirm all English-market ad accounts (Google Ads, TikTok Ads Manager, Meta IG-Influencer line items) are connected and that spend rows are joined to the same channel-3 keys used for conversions. Also check whether 'Youtube Ads' spend is being booked under 'Google Ads' at source.",
            "priority": "Critical",
        },
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
        "spend_tracking_integrity": spend_tracking,
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
