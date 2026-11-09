"""
Data Loader — shared utility for all analysis scripts.

Loads data/data.xlsx, cleans it, and adds derived columns used across all five
analysis questions. Returns two DataFrames:
  - df_full: all 1,152 rows (used for spend/subscriber analysis)
  - df_conv: the 434 rows that have non-null conversion + revenue data

Key assumptions:
- UNKNOWN market/channel rows are tagged but kept in df_full; excluded from df_conv
- Revenue uses New Revenue Invoice Date (confirmed payments) for all ROAS calculations
- ROAS = revenue_create_date / marketing_spendings (only where spend > 0)
- Cost per Subscriber = marketing_spendings / subscriber (only where spend > 0)
- Monthly name mapping uses standard Python calendar month abbreviations
"""

import os
import pandas as pd
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "data.xlsx")

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}


def load_data():
    """Return (df_full, df_conv) with derived columns added."""
    df = pd.read_excel(DATA_PATH)

    # Normalise column names
    df.columns = [c.strip() for c in df.columns]

    # Anonymise: the raw data labels the company's own podcast with the brand name
    # ("<Brand> Podcast"). Any podcast channel other than "Influencer Podcast" is
    # the owned one, so relabel it without spelling out the brand.
    channel_cols = [c for c in df.columns if c.startswith("Conversion Channel")]
    df[channel_cols] = df[channel_cols].replace(
        to_replace=r"^\s*(?!Influencer\b)\S+\s+Podcast\s*$", value="Owned Podcast", regex=True
    )

    # Derived columns
    df["month_name"] = df["Business Month"].map(MONTH_NAMES)
    df["is_unknown"] = (
        (df["Market"] == "UNKNOWN") |
        (df["Conversion Channel 1"] == "UNKNOWN") |
        (df["Conversion Channel 2"] == "UNKNOWN") |
        (df["Conversion Channel 3"].str.strip() == "UNKNOWN")
    )

    # Clamp coupon shares to [0, 1] — one known anomaly in the dataset (PR/English/Feb)
    # has Share Coupon Used = 1.3333, which is impossible for a ratio. Clamped here;
    # flagged by validate_data.py as a warning for the data team.
    for col in ["Share Coupon Used", "Share Student Coupon Used"]:
        df[col] = df[col].clip(upper=1.0)

    # Total conversions (monthly + yearly, where available)
    df["total_conversions"] = df["Monthly Conversions"].fillna(0) + df["Yearly Conversions"].fillna(0)

    # Loose CAC using all trial starters as denominator (Subscriber column = everyone
    # who started a subscription, including free trials who never paid).
    # NOTE: dashboard_data.py computes the stricter CAC used in the UI:
    #   spend / (Monthly Paid + Yearly Paid Conversions) — confirmed paying customers only.
    # This column exists for exploratory use; do not use it for CEO-facing metrics.
    df["cac_loose"] = np.where(
        (df["Marketing Spendings"] > 0) & (df["Subscriber"] > 0),
        df["Marketing Spendings"] / df["Subscriber"],
        np.nan
    )

    # ROAS: confirmed revenue (Invoice Date) per unit of spend.
    # Invoice Date = revenue from customers who actually paid.
    # Create Date would include trial starters who may never pay, overstating ROAS.
    df["roas"] = np.where(
        df["Marketing Spendings"] > 0,
        df["New Revenue Invoice Date"].fillna(0) / df["Marketing Spendings"],
        np.nan
    )

    # Revenue per subscriber (Invoice Date — confirmed payments only)
    df["revenue_per_subscriber"] = np.where(
        df["Subscriber"] > 0,
        df["New Revenue Invoice Date"].fillna(0) / df["Subscriber"],
        np.nan
    )

    # Conversion rate: total_conversions / subscriber (for rows with both)
    df["conversion_rate"] = np.where(
        df["Subscriber"] > 0,
        df["total_conversions"] / df["Subscriber"],
        np.nan
    )

    # df_conv: rows with meaningful conversion data (non-null Monthly + Yearly conversions)
    df_conv = df[
        df["Monthly Conversions"].notna() &
        df["Yearly Conversions"].notna() &
        (~df["is_unknown"])
    ].copy()

    return df, df_conv


if __name__ == "__main__":
    df_full, df_conv = load_data()
    print(f"Full dataset: {len(df_full)} rows")
    print(f"Conversion dataset: {len(df_conv)} rows")
    print(f"Markets: {df_full['Market'].unique().tolist()}")
    print(f"Channel 2 types: {df_full['Conversion Channel 2'].unique().tolist()}")
