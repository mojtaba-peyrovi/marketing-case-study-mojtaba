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
| 4 | **Key Patterns & Anomalies** — Efficiency gap, Meta deep-dive, trial-to-paid by channel |
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
