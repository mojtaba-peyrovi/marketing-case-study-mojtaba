# Marketing Campaign Analysis

An editorial-style data analysis case study presenting 2024 marketing campaign insights
to the CEO of a subscription-based audio content platform. Built as a fully
containerized web application with interactive charts and a magazine-style UI.

## Live Demo

**https://marketing-case-study-mojtaba-t4j662qnoa-ew.a.run.app** (GCP Cloud Run, europe-west1)

## Quick Start

```bash
git clone https://github.com/mojtaba-peyrovi/marketing-case-study-mojtaba.git
cd marketing-case-study-mojtaba
docker compose up --build
# open http://localhost:8080
```

## What It Answers

| # | Deliverable |
|---|-------------|
| 1 | **Executive Summary** — KPIs, top findings, blended ROAS |
| 2 | **Recommendations & Visualizations** — Actionable steps with Chart.js charts |
| 3 | **Budget Allocation Hypotheses** — Channel P&L with Scale / Reduce / Kill verdicts |
| 4 | **Key Patterns & Anomalies** — Cost-vs-quality quadrant scatter; named outliers (in-chart spotlights + extreme exclusions) |
| 5 | **Data Gaps & Additional Inputs** — What data would sharpen the analysis |

## Analysis Pipeline

All analysis runs **at Docker build time** via `analysis/generate_all.py`. No raw data is
processed at runtime — the web server only serves pre-computed JSON and static assets.

| Script | Output |
|--------|--------|
| `data_loader.py` | Shared DataFrame with computed columns (CAC, ROAS, conversion_rate) |
| `01_executive_summary.py` | `output/data/executive_summary.json` |
| `02_recommendations.py` | `output/data/recommendations.json` + 4 PNG charts |
| `03_budget_allocation.py` | `output/data/budget_allocation.json` + 2 PNG charts |
| `04_patterns_anomalies.py` | `output/data/patterns_anomalies.json` + 3 PNG charts |
| `05_data_gaps.py` | `output/data/data_gaps.json` |
| `dashboard_data.py` | `output/data/dashboard.json` — all KPIs and series for the UI |

> **CAC convention:** `Marketing Spend / (Monthly Paid + Yearly Paid Conversions)` —
> post-trial CAC, the industry standard for paid-channel evaluation.

## Data Validation & Testing

The build pipeline has two automated safety layers that run **before** any analysis output
is generated. If either layer fails, the Docker build stops and no report is produced.

### Layer 1 — Metric unit tests (`tests/test_metrics.py`)

11 tests that verify every formula used in the analysis against a small hand-crafted
DataFrame where the expected answer can be checked by mental arithmetic.

| Test | Formula verified |
|------|-----------------|
| `test_cac_paid_channel` | CAC = spend / (monthly paid + yearly paid conversions) |
| `test_cac_zero_spend_returns_nan` | Non-paid channels have no CAC (not zero) |
| `test_roas_paid_channel` | ROAS = revenue (create date) / spend |
| `test_roas_zero_spend_is_undefined` | ROAS undefined for zero-spend channels |
| `test_trial_to_paid` | Trial-to-paid = yearly paid / yearly conversions |
| `test_trial_to_paid_max_one` | Paid conversions can never exceed total conversions |
| `test_blended_roas` | Blended ROAS = total invoice revenue / total spend |
| `test_revenue_per_subscriber` | Revenue per subscriber = revenue / subscriber count |
| `test_total_subscribers_is_sum` | Aggregate totals match row-level sums |
| `test_paid_conversions_sum` | `paid_conversions` = monthly paid + yearly paid |
| `test_coupon_share_in_range` | Coupon shares are between 0 and 1 (0%–100%) |

Run locally:
```bash
python tests/test_metrics.py
```

### Layer 2 — Raw data validation (`analysis/validate_data.py`)

Checks the raw Excel file for structural and logical integrity before any analysis runs.

| Check | What it catches |
|-------|----------------|
| Required columns present | Missing or renamed columns in a new data file |
| All 12 months represented | Incomplete data exports |
| At least 3 known markets | Dropped or renamed market labels |
| No negative marketing spend | Data entry errors |
| No negative subscriber counts | Data entry errors |
| Coupon shares between 0–1 | Encoding errors (shares stored as counts, etc.) |
| Yearly paid ≤ yearly conversions | Logical impossibility in conversion data |
| No completely empty rows | Blank rows in the source file |

**Hard stop** (build fails, error printed): columns missing, negative values, logical
impossibilities, or values so far out of range they indicate serious corruption.

**Warning** (build continues, row flagged for the data team): values slightly above
expected range that appear to be isolated data entry artefacts. Example: one row in
the current dataset has `Share Coupon Used = 1.3333` (PR / English / February) — this
is flagged, clamped to 1.0 for analysis, and should be investigated with the data team.

Run locally:
```bash
python analysis/validate_data.py
```

### Build order in Docker

```
1. python tests/test_metrics.py      # formulas correct?
2. python analysis/generate_all.py   # data valid? → then generate outputs
```

If either step exits with an error, the build fails and the broken image is never
deployed to Cloud Run.

## CI/CD Setup (GitHub Actions → Cloud Run)

1. Enable GCP APIs:
   ```bash
   gcloud services enable run.googleapis.com artifactregistry.googleapis.com
   ```

2. Create an Artifact Registry Docker repository:
   ```bash
   gcloud artifacts repositories create marketing-case-study-mojtaba \
     --repository-format=docker \
     --location=europe-west1
   ```

3. Create a Service Account with roles:
   - `roles/run.admin`
   - `roles/artifactregistry.writer`
   - `roles/iam.serviceAccountUser`

4. Add GitHub repository secrets:
   - `GCP_PROJECT_ID` — your GCP project ID
   - `GCP_SA_KEY` — JSON key of the Service Account

5. Push to `main` — GitHub Actions builds the Docker image, pushes to Artifact Registry,
   and deploys to Cloud Run automatically.

## Tech Stack

- **Analysis:** Python, pandas, numpy, matplotlib, seaborn, scipy
- **Charts (UI):** Chart.js 4.4 (interactive, client-side)
- **Web:** Flask, Jinja2, HTML/CSS/JS
- **Typography:** Fraunces (display serif) + Inter (body sans-serif) via Google Fonts
- **Container:** Docker (`python:3.12-slim`)
- **Registry:** GCP Artifact Registry (`europe-west1-docker.pkg.dev`)
- **Hosting:** GCP Cloud Run (europe-west1, 512 Mi)
- **CI/CD:** GitHub Actions

## Privacy

Since this analysis involves sensitive subscriber and revenue data, the solution is fully
containerized. All data processing occurs inside the Docker container at build time.
No raw data is exposed via web routes at runtime, and AI coding agents had zero access
to the raw dataset outside the container environment — ensuring 100% data privacy.
