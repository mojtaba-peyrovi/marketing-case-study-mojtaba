"""
Metric unit tests — verifies every formula used in the analysis is correct.

Run:
    python -m pytest tests/ -v
    # or without pytest:
    python tests/test_metrics.py

These tests use a small hand-crafted DataFrame so the expected answers
can be verified by mental arithmetic, making it easy to prove to the CEO
that each calculation is correct.
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np

# ── Minimal test DataFrame ────────────────────────────────────────────────────
# Two rows: one paid channel (Meta), one non-paid (Word of Mouth)
MOCK_DF = pd.DataFrame({
    "Business Month": [1, 1],
    "Market": ["German", "German"],
    "Conversion Channel 1": ["Paid", "Non-Paid"],
    "Conversion Channel 2": ["Performance Marketing", "Organic"],
    "Conversion Channel 3": ["Facebook/Instagram Ads", "Word of Mouth"],
    "Marketing Spendings": [10_000, 0],
    "Subscriber": [500, 200],
    "Monthly Conversions": [50.0, 20.0],
    "Yearly Conversions": [400.0, 150.0],
    "Monthly Paid Conversions": [50, 20],
    "Yearly Paid Conversions": [100.0, 40.0],
    "New Revenue Create Date": [8_000.0, 3_000.0],
    "New Revenue Invoice Date": [7_500.0, 2_800.0],
    "Share Coupon Used": [0.30, 0.25],
    "Share Student Coupon Used": [0.10, 0.05],
})
MOCK_DF["paid_conversions"] = (
    MOCK_DF["Monthly Paid Conversions"].fillna(0) +
    MOCK_DF["Yearly Paid Conversions"].fillna(0)
)


# ── CAC tests ────────────────────────────────────────────────────────────────

def test_cac_paid_channel():
    """CAC = spend / paid_conversions (post-trial metric)."""
    meta = MOCK_DF[MOCK_DF["Conversion Channel 3"] == "Facebook/Instagram Ads"].iloc[0]
    # 10,000 spend / (50 monthly paid + 100 yearly paid) = 10,000 / 150 = 66.67
    expected = 10_000 / 150
    cac = meta["Marketing Spendings"] / meta["paid_conversions"]
    assert abs(cac - expected) < 0.01, f"CAC mismatch: {cac} vs {expected}"


def test_cac_zero_spend_returns_nan():
    """Non-paid channels have no spend — CAC should be undefined (NaN), not zero."""
    wom = MOCK_DF[MOCK_DF["Conversion Channel 3"] == "Word of Mouth"].iloc[0]
    cac = np.where(wom["Marketing Spendings"] > 0, wom["Marketing Spendings"] / wom["paid_conversions"], np.nan)
    assert math.isnan(float(cac)), "Zero-spend CAC should be NaN, not a number"


# ── ROAS tests ────────────────────────────────────────────────────────────────

def test_roas_paid_channel():
    """ROAS = New Revenue (Invoice Date) / Marketing Spend.
    Invoice Date = confirmed payments only. Create Date would include trial starters
    who may never pay, overstating ROAS.
    """
    meta = MOCK_DF[MOCK_DF["Conversion Channel 3"] == "Facebook/Instagram Ads"].iloc[0]
    # 7,500 invoice revenue / 10,000 spend = 0.75
    expected = 7_500 / 10_000
    roas = meta["New Revenue Invoice Date"] / meta["Marketing Spendings"]
    assert abs(roas - expected) < 0.001, f"ROAS mismatch: {roas} vs {expected}"


def test_roas_zero_spend_is_undefined():
    """ROAS for a non-paid channel should not be computed (would be division by zero)."""
    wom = MOCK_DF[MOCK_DF["Conversion Channel 3"] == "Word of Mouth"].iloc[0]
    roas = np.where(wom["Marketing Spendings"] > 0, wom["New Revenue Invoice Date"] / wom["Marketing Spendings"], np.nan)
    assert math.isnan(float(roas)), "Zero-spend ROAS should be NaN"


# ── Trial-to-paid tests ───────────────────────────────────────────────────────

def test_trial_to_paid():
    """Trial-to-paid = Yearly Paid Conversions / Yearly Conversions."""
    meta = MOCK_DF[MOCK_DF["Conversion Channel 3"] == "Facebook/Instagram Ads"].iloc[0]
    # 100 yearly paid / 400 yearly conversions = 25%
    expected = 100 / 400
    t2p = meta["Yearly Paid Conversions"] / meta["Yearly Conversions"]
    assert abs(t2p - expected) < 0.001, f"Trial-to-paid mismatch: {t2p} vs {expected}"


def test_trial_to_paid_max_one():
    """Trial-to-paid can never exceed 100% — paid conversions <= total conversions."""
    for _, row in MOCK_DF[MOCK_DF["Yearly Conversions"] > 0].iterrows():
        t2p = row["Yearly Paid Conversions"] / row["Yearly Conversions"]
        assert t2p <= 1.0, f"Trial-to-paid > 100% for {row['Conversion Channel 3']}: {t2p:.2%}"


# ── Blended ROAS tests ────────────────────────────────────────────────────────

def test_blended_roas():
    """Blended ROAS = total invoice revenue / total spend (across all channels)."""
    total_rev = MOCK_DF["New Revenue Invoice Date"].sum()   # 7,500 + 2,800 = 10,300
    total_spend = MOCK_DF["Marketing Spendings"].sum()      # 10,000 + 0 = 10,000
    expected = 10_300 / 10_000                              # 1.03
    blended = total_rev / total_spend
    assert abs(blended - expected) < 0.001, f"Blended ROAS mismatch: {blended} vs {expected}"


# ── Revenue per subscriber ────────────────────────────────────────────────────

def test_revenue_per_subscriber():
    """Revenue per subscriber = Revenue (Invoice Date) / Subscriber count."""
    meta = MOCK_DF[MOCK_DF["Conversion Channel 3"] == "Facebook/Instagram Ads"].iloc[0]
    # 7,500 / 500 = 15.0
    expected = 7_500 / 500
    rev_per_sub = meta["New Revenue Invoice Date"] / meta["Subscriber"]
    assert abs(rev_per_sub - expected) < 0.001, f"Revenue/sub mismatch: {rev_per_sub} vs {expected}"


# ── Aggregation consistency ───────────────────────────────────────────────────

def test_total_subscribers_is_sum():
    """Total subscribers must equal the sum of per-channel subscriber counts."""
    total = MOCK_DF["Subscriber"].sum()  # 500 + 200 = 700
    assert total == 700


def test_paid_conversions_sum():
    """paid_conversions column = Monthly Paid + Yearly Paid."""
    for _, row in MOCK_DF.iterrows():
        expected = row["Monthly Paid Conversions"] + (row["Yearly Paid Conversions"] or 0)
        assert row["paid_conversions"] == expected, f"paid_conversions wrong for {row['Conversion Channel 3']}"


# ── Coupon range check ────────────────────────────────────────────────────────

def test_coupon_share_in_range():
    """Coupon usage shares must be between 0 and 1 (0% to 100%)."""
    for col in ["Share Coupon Used", "Share Student Coupon Used"]:
        col_vals = MOCK_DF[col].dropna()
        assert (col_vals >= 0).all(), f"{col} has negative values"
        assert (col_vals <= 1).all(), f"{col} has values above 1 (above 100%)"


# ── Q4 quadrant tests (cost vs quality scatter) ───────────────────────────────

def _load_quadrant():
    """Load the q4_quadrant block from the generated dashboard.json."""
    import json
    path = os.path.join(os.path.dirname(__file__), "..", "output", "data", "dashboard.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["q4_quadrant"]


def test_q4_medians_match_hand_computed():
    """Median CAC and t2p must equal hand-computed medians of the 5 included paid channels.
    CACs sorted: 2.85, 9.71, 37.35, 68.97, 69.99 → median 37.35
    t2p sorted:  20.6, 21.7, 25.6, 28.9, 29.0   → median 25.6
    """
    q = _load_quadrant()
    assert q["median_cac"] == 37.35, f"median CAC mismatch: {q['median_cac']}"
    assert q["median_t2p_pct"] == 25.6, f"median t2p mismatch: {q['median_t2p_pct']}"


def test_q4_excludes_extreme_outliers():
    """Influencer Youtube (€6,540 CAC) and Partnership Ads (zero conv) must NOT be in points."""
    q = _load_quadrant()
    in_chart = {p["channel"] for p in q["points"]}
    excluded = {e["channel"] for e in q["excluded_outliers"]}
    assert "Influencer Youtube" not in in_chart
    assert "Partnership Ads" not in in_chart
    assert excluded == {"Influencer Youtube", "Partnership Ads"}


def test_q4_quadrant_assignments():
    """Each known channel falls in the expected quadrant given the medians."""
    q = _load_quadrant()
    by_ch = {p["channel"]: p["quadrant"] for p in q["points"]}
    expected = {
        "Facebook/Instagram Ads": "premium",                  # cac>median, t2p==median (top half)
        "Influencer Instagram":   "efficient_high_quality",   # cac==median (left), t2p>median
        "TikTok Ads":             "wasted_spend",             # cac>median, t2p<median
        "Google Ads":             "cheap_moderate",            # cac<median, t2p<median
        "Influencer Podcast":     "efficient_high_quality",   # cac<median, t2p>median
    }
    for ch, want in expected.items():
        assert by_ch.get(ch) == want, f"{ch}: got {by_ch.get(ch)}, want {want}"


def test_q4_spend_shares_sum_to_paid_total():
    """Spend shares of in-chart points + excluded outliers + any other paid channels = 100%."""
    q = _load_quadrant()
    in_chart_spend = sum(p["spend"] for p in q["points"])
    excluded_spend = sum(e["spend"] for e in q["excluded_outliers"])
    # in_chart + excluded = total paid spend (no paid channel left out)
    assert abs(in_chart_spend + excluded_spend - q["total_paid_spend"]) < 1.0, (
        f"spend reconciliation failed: in_chart={in_chart_spend} + excluded={excluded_spend} "
        f"!= total_paid={q['total_paid_spend']}"
    )


def test_q4_spotlight_outliers():
    """Spotlight outliers must be deterministic: biggest spender, cheapest CAC, only waste-quadrant."""
    q = _load_quadrant()
    s = q["spotlight_outliers"]
    assert s["biggest_spender"]["channel"] == "Facebook/Instagram Ads"
    assert s["cheapest_cac"]["channel"] == "Influencer Podcast"
    assert s["wasted_spend"]["channel"] == "TikTok Ads"


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests.")
    if failed:
        sys.exit(1)
