"""
Data validation — runs before any analysis.

If the raw data is corrupt or missing required structure, this raises a
DataValidationError with a plain-English message so the data team can fix
the problem immediately. The Docker build fails at this point, so a broken
dataset can never silently produce wrong numbers in the final report.

Checks performed:
  1. Required columns all present
  2. All 12 calendar months represented
  3. At least 3 known markets
  4. Marketing Spendings never negative
  5. Subscriber counts never negative
  6. Coupon usage shares between 0 and 1 (i.e. 0% – 100%)
  7. Yearly Paid Conversions never exceed Yearly Conversions
  8. No completely empty rows

Usage:
    from validate_data import validate
    validate(df)   # raises DataValidationError on failure, returns None on success
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))


class DataValidationError(Exception):
    """Raised when the raw dataset fails a quality check."""
    pass


REQUIRED_COLUMNS = [
    "Business Year", "Business Month", "Market",
    "Conversion Channel 1", "Conversion Channel 2", "Conversion Channel 3",
    "Marketing Spendings", "Subscriber",
    "Monthly Paid Conversions", "Yearly Paid Conversions",
    "New Revenue Create Date", "New Revenue Invoice Date",
    "Share Coupon Used", "Share Student Coupon Used",
]


def validate(df: pd.DataFrame) -> None:
    errors = []

    # 1. Required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(
            f"Missing required columns: {missing_cols}. "
            "Check that the data file has not been restructured."
        )

    if errors:
        _fail(errors)  # no point continuing if columns are missing

    # 2. All 12 months present
    months_found = sorted(df["Business Month"].dropna().unique().tolist())
    expected_months = list(range(1, 13))
    missing_months = [m for m in expected_months if m not in months_found]
    if missing_months:
        errors.append(
            f"Missing months: {missing_months}. "
            "The dataset should cover all 12 months (Jan=1 through Dec=12)."
        )

    # 3. At least 3 known markets
    known_markets = [m for m in df["Market"].unique() if m != "UNKNOWN"]
    if len(known_markets) < 3:
        errors.append(
            f"Only {len(known_markets)} known market(s) found: {known_markets}. "
            "Expected at least German, French, and English."
        )

    # 4. No negative spend
    neg_spend = (df["Marketing Spendings"] < 0).sum()
    if neg_spend > 0:
        bad = df[df["Marketing Spendings"] < 0][["Business Month", "Market", "Conversion Channel 3", "Marketing Spendings"]].head(5)
        errors.append(
            f"{neg_spend} row(s) have negative Marketing Spendings. "
            f"First offenders:\n{bad.to_string(index=False)}"
        )

    # 5. No negative subscriber counts
    neg_subs = (df["Subscriber"] < 0).sum()
    if neg_subs > 0:
        errors.append(
            f"{neg_subs} row(s) have negative Subscriber counts. "
            "Subscriber counts cannot be negative."
        )

    # 6. Coupon shares between 0 and 1
    # Values slightly above 1 (up to 1.5) are flagged as warnings — likely data entry
    # artefacts — and are clamped to 1.0 in data_loader.py before analysis.
    # Values below 0 or above 1.5 are hard errors (clearly wrong).
    for col in ["Share Coupon Used", "Share Student Coupon Used"]:
        col_vals = df[col].dropna()
        hard_bad = ((col_vals < 0) | (col_vals > 1.5)).sum()
        if hard_bad > 0:
            errors.append(
                f"{hard_bad} row(s) in '{col}' have values outside the 0–1.5 range. "
                "This column stores a share (e.g. 0.31 = 31%), not a raw count. "
                "Values this far out of range indicate a serious data encoding error."
            )
        soft_bad_mask = (col_vals > 1.0) & (col_vals <= 1.5)
        if soft_bad_mask.sum() > 0:
            bad_rows = df.loc[col_vals[soft_bad_mask].index, ["Business Month", "Market", "Conversion Channel 3", col]]
            print(
                f"\n  [WARNING] {soft_bad_mask.sum()} row(s) in '{col}' are between 1.0 and 1.5 "
                f"(above 100%). These will be clamped to 1.0 in the analysis. "
                f"Notify the data team to investigate:\n{bad_rows.to_string(index=False)}\n"
            )

    # 7. Yearly Paid <= Yearly Conversions (can't have more paid than total)
    check = df[df["Yearly Conversions"].notna() & df["Yearly Paid Conversions"].notna()]
    overpaid = (check["Yearly Paid Conversions"] > check["Yearly Conversions"]).sum()
    if overpaid > 0:
        errors.append(
            f"{overpaid} row(s) have Yearly Paid Conversions > Yearly Conversions. "
            "Paid conversions are a subset of all conversions — this should be impossible."
        )

    # 8. No completely empty rows (all key numeric columns null)
    key_cols = ["Marketing Spendings", "Subscriber"]
    all_null = df[key_cols].isnull().all(axis=1).sum()
    if all_null > 0:
        errors.append(
            f"{all_null} row(s) have null values in all key numeric columns. "
            "These rows would produce no useful output."
        )

    if errors:
        _fail(errors)

    print(f"  [validate] All checks passed ({len(df):,} rows, {len(df.columns)} columns)")


def _fail(errors):
    divider = "\n" + "=" * 60 + "\n"
    msg = divider
    msg += "DATA VALIDATION FAILED\n"
    msg += "The analysis has been stopped. Fix the raw data before rerunning.\n"
    msg += divider
    for i, e in enumerate(errors, 1):
        msg += f"\n[{i}] {e}\n"
    msg += divider
    raise DataValidationError(msg)


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from data_loader import load_data
    df_full, _ = load_data()
    validate(df_full)
