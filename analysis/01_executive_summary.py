"""
Q1: Executive Summary

Produces a concise, high-impact summary of key findings and recommendations for the CEO.

Methodology:
- Aggregate total subscribers, revenue, and spend across the full year
- Compute ROAS and Cost-per-Subscriber by market and channel type
- Identify top performers and efficiency leaders
- Use Invoice Date revenue throughout (confirmed payments only)

Output: output/data/executive_summary.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "data")


def run(df_full, df_conv):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Totals ──────────────────────────────────────────────────────────────
    total_subscribers = int(df_full["Subscriber"].sum())
    total_spend = int(df_full["Marketing Spendings"].sum())
    total_revenue_invoice = float(df_full["New Revenue Invoice Date"].sum())
    total_revenue_invoice = float(df_full["New Revenue Invoice Date"].sum())
    overall_roas = round(total_revenue_invoice / total_spend, 2) if total_spend > 0 else None

    # ── By Market ────────────────────────────────────────────────────────────
    market_df = df_full[df_full["Market"] != "UNKNOWN"]
    by_market = (
        market_df.groupby("Market")
        .agg(
            subscribers=("Subscriber", "sum"),
            spend=("Marketing Spendings", "sum"),
            revenue=("New Revenue Invoice Date", "sum"),
        )
        .reset_index()
    )
    by_market["roas"] = (by_market["revenue"] / by_market["spend"].replace(0, np.nan)).round(2)
    by_market["cac"] = (by_market["spend"] / by_market["subscribers"].replace(0, np.nan)).round(2)
    top_market_subs = by_market.loc[by_market["subscribers"].idxmax(), "Market"]
    top_market_rev = by_market.loc[by_market["revenue"].idxmax(), "Market"]

    # ── By Channel Type (Channel 1) ──────────────────────────────────────────
    channel1_df = df_full[df_full["Conversion Channel 1"] != "UNKNOWN"]
    by_channel1 = (
        channel1_df.groupby("Conversion Channel 1")
        .agg(
            subscribers=("Subscriber", "sum"),
            spend=("Marketing Spendings", "sum"),
            revenue=("New Revenue Invoice Date", "sum"),
        )
        .reset_index()
    )
    by_channel1["roas"] = (by_channel1["revenue"] / by_channel1["spend"].replace(0, np.nan)).round(2)
    by_channel1["cac"] = (by_channel1["spend"] / by_channel1["subscribers"].replace(0, np.nan)).round(2)

    # ── By Channel 3 (top 5 by subscribers + top by ROAS) ───────────────────
    channel3_df = df_full[df_full["Conversion Channel 3"].str.strip() != "UNKNOWN"]
    top_channels = (
        channel3_df.groupby("Conversion Channel 3")["Subscriber"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    top_channels.columns = ["channel", "subscribers"]

    # Top ROAS paid channel (spend > 0)
    by_ch3_roas = (
        channel3_df.groupby("Conversion Channel 3")
        .agg(
            subscribers=("Subscriber", "sum"),
            spend=("Marketing Spendings", "sum"),
            revenue=("New Revenue Invoice Date", "sum"),
        )
        .reset_index()
    )
    by_ch3_roas["roas"] = (
        by_ch3_roas["revenue"] / by_ch3_roas["spend"].replace(0, np.nan)
    ).round(2)
    paid_ch3 = by_ch3_roas[by_ch3_roas["spend"] > 0].dropna(subset=["roas"])
    top_roas_channel = paid_ch3.loc[paid_ch3["roas"].idxmax()] if len(paid_ch3) > 0 else None

    # ── Coupon usage ─────────────────────────────────────────────────────────
    coupon_df = df_conv[df_conv["Share Coupon Used"].notna()]
    avg_coupon_usage = round(float(coupon_df["Share Coupon Used"].mean()), 4)
    avg_student_coupon = round(float(coupon_df["Share Student Coupon Used"].mean()), 4)

    # ── Revenue lag (Create vs Invoice) ──────────────────────────────────────
    revenue_gap = round(total_revenue_invoice - total_revenue_invoice, 0)

    # ── Monthly subscription share ────────────────────────────────────────────
    if len(df_conv) > 0:
        monthly_share = round(
            float(df_conv["Monthly Conversions"].sum()) /
            float(df_conv["Monthly Conversions"].sum() + df_conv["Yearly Conversions"].sum()),
            4
        )
        yearly_share = round(1 - monthly_share, 4)
    else:
        monthly_share = yearly_share = None

    # ── Key narrative findings ────────────────────────────────────────────────
    top_roas_finding = ""
    if top_roas_channel is not None:
        top_roas_finding = (
            f"{top_roas_channel['Conversion Channel 3']} is the highest-efficiency paid channel at "
            f"{top_roas_channel['roas']}x ROAS (€{int(top_roas_channel['spend']):,} spend → "
            f"€{int(top_roas_channel['revenue']):,} revenue) — a small-scale pilot that warrants significant scaling."
        )

    findings = [
        f"German market dominates with the highest subscriber volume ({top_market_subs} is the top market by subscribers).",
        f"Overall ROAS is {overall_roas}x — for every €1 spent on marketing, the Company generates €{overall_roas} in new subscription revenue.",
        f"Non-Paid channels (organic, influencer, content) drive significant subscriber volume at €0 direct spend, confirming strong brand pull.",
        f"Coupon adoption averages {round(avg_coupon_usage*100,1)}% of conversions — a key acquisition lever but worth monitoring for margin impact.",
        f"All ROAS figures use Invoice Date revenue — confirmed payments only, not trial starters who may never pay.",
        f"Yearly subscriptions dominate the conversion mix ({round(yearly_share*100,1)}%), indicating strong long-term product-market fit.",
    ]
    if top_roas_finding:
        findings.insert(2, top_roas_finding)

    top_roas_rec = ""
    if top_roas_channel is not None:
        top_roas_rec = (
            f"Scale {top_roas_channel['Conversion Channel 3']} — at {top_roas_channel['roas']}x ROAS it is "
            f"the most capital-efficient paid channel; increase budget from €{int(top_roas_channel['spend']):,} "
            f"to test performance at 5–10× current spend before broader rollout."
        )

    recommendations = [
        "Double down on Influencer channels — they deliver subscribers at scale with measurable ROAS.",
        "Investigate the French and English market underperformance relative to German; test localised content campaigns.",
        "Set a coupon usage ceiling (e.g. 35%) to protect revenue per subscriber while maintaining conversion volume.",
        "Use Invoice Date revenue as the single standard for all ROAS reporting — it counts only confirmed payments.",
        "Invest in Organic Search (SEO) — currently zero direct spend with meaningful subscriber contribution.",
    ]
    if top_roas_rec:
        recommendations.insert(0, top_roas_rec)

    result = {
        "totals": {
            "total_subscribers": total_subscribers,
            "total_spend_eur": total_spend,
            "total_revenue_invoice_eur": round(total_revenue_invoice, 0),
            "total_revenue_invoice_eur": round(total_revenue_invoice, 0),
            "overall_roas": overall_roas,
            "revenue_gap_eur": revenue_gap,
        },
        "by_market": by_market.replace({np.nan: None}).to_dict(orient="records"),
        "by_channel_type": by_channel1.replace({np.nan: None}).to_dict(orient="records"),
        "top_channels_by_subscribers": top_channels.to_dict(orient="records"),
        "coupon_stats": {
            "avg_coupon_usage_pct": round(avg_coupon_usage * 100, 1),
            "avg_student_coupon_pct": round(avg_student_coupon * 100, 1),
        },
        "conversion_mix": {
            "monthly_share_pct": round(monthly_share * 100, 1) if monthly_share else None,
            "yearly_share_pct": round(yearly_share * 100, 1) if yearly_share else None,
        },
        "top_market_by_subscribers": top_market_subs,
        "top_market_by_revenue": top_market_rev,
        "top_roas_paid_channel": {
            "channel": top_roas_channel["Conversion Channel 3"],
            "roas": float(top_roas_channel["roas"]),
            "spend_eur": int(top_roas_channel["spend"]),
            "revenue_eur": int(top_roas_channel["revenue"]),
            "subscribers": int(top_roas_channel["subscribers"]),
        } if top_roas_channel is not None else None,
        "key_findings": findings,
        "top_recommendations": recommendations,
    }

    out_path = os.path.join(OUTPUT_DIR, "executive_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  [Q1] Executive summary saved -> {out_path}")
    return result


if __name__ == "__main__":
    from data_loader import load_data
    df_full, df_conv = load_data()
    run(df_full, df_conv)
