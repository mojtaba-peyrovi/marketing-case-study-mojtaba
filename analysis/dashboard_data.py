"""
Dashboard data — produces a single dashboard.json containing every metric
the editorial UI needs (KPIs, monthly indexed series, Meta deep-dive,
channel P&L, trial-to-paid, market cards, reallocation table).

CAC convention here:  CAC = Marketing Spend / (Monthly Paid + Yearly Paid Conversions)
This is a stricter post-trial CAC (excludes trial-only subscribers) and is the
industry standard for paid-channel evaluation.

ROAS convention: New Revenue (Invoice Date) / Marketing Spend.
Invoice Date is used because it represents revenue actually received (confirmed payments).
Create Date includes trial starters who may never pay, which would overstate ROAS.
Trial-to-paid:   Yearly Paid Conversions / Yearly Conversions (per channel).
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
OUTPUT_DATA = os.path.join(os.path.dirname(__file__), "..", "output", "data")


def _safe(v, fallback=0):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return fallback
    return v


def _verdict(channel, spend, cac, roas, t2p, full_year_paid_share):
    """Classification rule for each channel based on CAC, ROAS, trial-to-paid, scale."""
    if channel in ("Influencer Youtube", "Partnership Ads"):
        return "Kill"
    if channel == "TikTok Ads":
        return "Paused"
    if spend == 0 or spend is None:
        return "Organic"
    if cac is None:
        return "Kill"
    if roas >= 3.0 and cac < 30:
        return "Scale"
    if roas >= 5.0:
        return "Test+"
    if roas < 0.6 and full_year_paid_share > 0.05:
        return "Reduce"
    if t2p is not None and t2p >= 28 and roas >= 0.85:
        return "Scale"
    return "Monitor"


def run(df_full, df_conv):
    os.makedirs(OUTPUT_DATA, exist_ok=True)

    df = df_full.copy()
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # ── Aggregations ────────────────────────────────────────────────────────
    df["paid_conversions"] = (
        df["Monthly Paid Conversions"].fillna(0) +
        df["Yearly Paid Conversions"].fillna(0)
    )

    total_spend = float(df["Marketing Spendings"].sum())
    total_subs = int(df["Subscriber"].sum())
    total_rev_invoice = float(df["New Revenue Invoice Date"].sum())
    # total_paid_conv = float(df["paid_conversions"].sum())
    blended_roas = round(total_rev_invoice / total_spend, 2) if total_spend else None

    # DACH+FR subscriber share
    dachfr_subs = int(df[df["Market"].isin(["German", "French"])]["Subscriber"].sum())
    dachfr_share_pct = round(dachfr_subs / total_subs * 100, 0)

    # ── Monthly time series ─────────────────────────────────────────────────
    monthly = df.groupby("Business Month").agg(
        spend=("Marketing Spendings", "sum"),
        paid_conv=("paid_conversions", "sum"),
        revenue=("New Revenue Invoice Date", "sum"),
    ).reindex(range(1, 13)).reset_index()

    spend_jan = float(monthly.iloc[0]["spend"])
    conv_jan = float(monthly.iloc[0]["paid_conv"])
    monthly["spend_idx"] = (monthly["spend"] / spend_jan * 100).round(0)
    monthly["conv_idx"] = (monthly["paid_conv"] / conv_jan * 100).round(0)

    spend_growth_pct = int(round((monthly.iloc[-1]["spend"] / spend_jan - 1) * 100))
    conv_growth_pct = int(round((monthly.iloc[-1]["paid_conv"] / conv_jan - 1) * 100))
    spend_vs_conv_multiplier = round(spend_growth_pct / conv_growth_pct, 1) if conv_growth_pct else None

    # Quarterly CAC
    df["quarter"] = pd.cut(df["Business Month"], bins=[0, 3, 6, 9, 12],
                           labels=["Q1", "Q2", "Q3", "Q4"])
    q = df.groupby("quarter", observed=True).agg(
        spend=("Marketing Spendings", "sum"),
        paid=("paid_conversions", "sum"),
        rev=("New Revenue Invoice Date", "sum"),
    )
    q["cac"] = (q["spend"] / q["paid"]).round(2)
    q["roas"] = (q["rev"] / q["spend"]).round(2)
    q1_cac = float(q.loc["Q1", "cac"])
    q4_cac = float(q.loc["Q4", "cac"])
    q1_roas = float(q.loc["Q1", "roas"])
    q4_roas = float(q.loc["Q4", "roas"])
    cac_inflation_pct = int(round((q4_cac / q1_cac - 1) * 100))

    # ── Meta deep dive ──────────────────────────────────────────────────────
    meta = df[df["Conversion Channel 3"] == "Facebook/Instagram Ads"]
    meta_monthly = meta.groupby("Business Month").agg(
        spend=("Marketing Spendings", "sum"),
        paid=("paid_conversions", "sum"),
    ).reindex(range(1, 13)).reset_index()
    meta_monthly["cac"] = (meta_monthly["spend"] / meta_monthly["paid"]).round(2)

    meta_total_spend = float(meta["Marketing Spendings"].sum())
    meta_total_paid = float(meta["paid_conversions"].sum())
    meta_total_rev = float(meta["New Revenue Invoice Date"].sum())
    meta_full_year_cac = round(meta_total_spend / meta_total_paid, 2)
    meta_full_year_roas = round(meta_total_rev / meta_total_spend, 2)
    paid_total_spend = float(df[df["Marketing Spendings"] > 0]["Marketing Spendings"].sum())
    meta_share_of_paid_pct = round(meta_total_spend / paid_total_spend * 100, 1)
    meta_jan_cac = float(meta_monthly.iloc[0]["cac"])
    meta_dec_cac = float(meta_monthly.iloc[-1]["cac"])
    meta_cac_inflation_pct = int(round((meta_dec_cac / meta_jan_cac - 1) * 100))
    meta_spend_growth_pct = int(round((meta_monthly.iloc[-1]["spend"] / meta_monthly.iloc[0]["spend"] - 1) * 100))

    # ── Channel P&L ──────────────────────────────────────────────────────────
    paid_df = df[df["Conversion Channel 3"].str.strip() != "UNKNOWN"]
    ch_agg = paid_df.groupby("Conversion Channel 3").agg(
        spend=("Marketing Spendings", "sum"),
        subs=("Subscriber", "sum"),
        paid=("paid_conversions", "sum"),
        rev=("New Revenue Invoice Date", "sum"),
        yc=("Yearly Conversions", "sum"),
        yp=("Yearly Paid Conversions", "sum"),
    ).reset_index().rename(columns={"Conversion Channel 3": "channel"})

    ch_agg["cac"] = np.where(
        (ch_agg["spend"] > 0) & (ch_agg["paid"] > 0),
        (ch_agg["spend"] / ch_agg["paid"]).round(2),
        None
    )
    ch_agg["roas"] = np.where(
        ch_agg["spend"] > 0,
        (ch_agg["rev"] / ch_agg["spend"]).round(2),
        None
    )
    ch_agg["t2p_pct"] = np.where(
        ch_agg["yc"] > 0,
        (ch_agg["yp"] / ch_agg["yc"] * 100).round(1),
        None
    )
    ch_agg["spend_share_pct"] = (ch_agg["spend"] / paid_total_spend * 100).round(2)

    # Channel P&L cards (paid channels only, sorted by spend desc)
    paid_channels_df = ch_agg[ch_agg["spend"] > 0].sort_values("spend", ascending=False)
    channel_cards = []
    for _, r in paid_channels_df.iterrows():
        v = _verdict(
            r["channel"],
            r["spend"], r["cac"], r["roas"], r["t2p_pct"],
            r["spend"] / paid_total_spend
        )
        channel_cards.append({
            "name": r["channel"],
            "spend": float(r["spend"]),
            "spend_share_pct": float(r["spend_share_pct"]),
            "cac": float(r["cac"]) if r["cac"] is not None else None,
            "roas": float(r["roas"]) if r["roas"] is not None else None,
            "t2p_pct": float(r["t2p_pct"]) if r["t2p_pct"] is not None else None,
            "verdict": v,
        })

    # Trial-to-paid chart: all channels with t2p, sorted desc, exclude very-low-volume.
    # Two categories only: paid media vs organic/earned — matches the narrative.
    PAID_CHANNELS = {
        "Facebook/Instagram Ads", "Google Ads",
        "Influencer Instagram", "Influencer Podcast",
        "TikTok Ads", "Youtube Ads",
    }
    t2p_data = []
    for _, r in ch_agg[(ch_agg["yc"] >= 50) & ch_agg["t2p_pct"].notna()].sort_values("t2p_pct", ascending=False).iterrows():
        ch = r["channel"]
        cat = "paid" if ch in PAID_CHANNELS else "organic"
        t2p_data.append({
            "channel": ch,
            "t2p_pct": float(r["t2p_pct"]),
            "category": cat,
        })

    # ── Markets ──────────────────────────────────────────────────────────────
    market_df = df[df["Market"].isin(["German", "French", "English"])]
    markets = []
    for m_name, code in [("German", "de"), ("French", "fr"), ("English", "en")]:
        md = market_df[market_df["Market"] == m_name]
        spend = float(md["Marketing Spendings"].sum())
        subs = int(md["Subscriber"].sum())
        paid = float(md["paid_conversions"].sum())
        rev_invoice = float(md["New Revenue Invoice Date"].sum())
        yc = float(md["Yearly Conversions"].sum())
        yp = float(md["Yearly Paid Conversions"].sum())
        cac = round(spend / paid, 2) if paid else None
        roas = round(rev_invoice / spend, 2) if spend else None
        t2p = round(yp / yc * 100, 1) if yc else None
        arpu = round(rev_invoice / paid, 2) if paid else None
        markets.append({
            "name": m_name,
            "code": code,
            "spend": spend,
            "subs": subs,
            "cac": cac,
            "roas": roas,
            "t2p_pct": t2p,
            "arpu": arpu,
        })

    # ── KPI strip ────────────────────────────────────────────────────────────
    kpis = {
        "total_spend": total_spend,
        "total_subs": total_subs,
        "total_rev_invoice": total_rev_invoice,
        "blended_roas": blended_roas,
        "spend_growth_pct": spend_growth_pct,
        "dachfr_share_pct": int(dachfr_share_pct),
    }

    # ── Output ───────────────────────────────────────────────────────────────
    result = {
        "kpis": kpis,
        "efficiency": {
            "months": months,
            "spend_idx": monthly["spend_idx"].tolist(),
            "conv_idx": monthly["conv_idx"].tolist(),
            "spend_growth_pct": spend_growth_pct,
            "conv_growth_pct": conv_growth_pct,
            "gap_pts": spend_growth_pct - conv_growth_pct,
            "spend_vs_conv_multiplier": spend_vs_conv_multiplier,
            "q1_cac": q1_cac,
            "q4_cac": q4_cac,
            "q1_roas": q1_roas,
            "q4_roas": q4_roas,
            "cac_inflation_pct": cac_inflation_pct,
        },
        "meta": {
            "months": months,
            "spend_series": [int(v) for v in meta_monthly["spend"].tolist()],
            "cac_series": [float(v) for v in meta_monthly["cac"].tolist()],
            "total_spend": meta_total_spend,
            "share_of_paid_pct": meta_share_of_paid_pct,
            "full_year_cac": meta_full_year_cac,
            "full_year_roas": meta_full_year_roas,
            "spend_growth_pct": meta_spend_growth_pct,
            "cac_inflation_pct": meta_cac_inflation_pct,
            "jan_cac": meta_jan_cac,
            "dec_cac": meta_dec_cac,
        },
        "channels": channel_cards,
        "trial_to_paid": t2p_data,
        "markets": markets,
    }

    out_path = os.path.join(OUTPUT_DATA, "dashboard.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=lambda x: None if pd.isna(x) else x)

    print(f"  [dashboard] saved -> {out_path}")
    return result


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_loader import load_data
    df_full, df_conv = load_data()
    run(df_full, df_conv)
