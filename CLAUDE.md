# Marketing Campaign Analysis — Case Study

## Project Overview

Senior Data Analyst case study, anonymized for public sharing (real company name and
identifying details replaced with "the Company"). Analyzes a 2024 Marketing Campaign
Performance Dataset (1,152 rows × 17 columns) across 4 markets and 24 conversion channels,
delivering CEO-level actionable insights via a branded web UI.

**Five deliverables answered:**
1. Executive Summary — key findings and recommendations
2. Recommendations & Visualizations — specific actions with supporting charts
3. Budget Allocation Hypotheses — where to increase or decrease spend
4. Key Patterns & Anomalies — trends, outliers, and implications
5. Data Gaps & Additional Inputs — what data would improve the analysis

**Stack:** Python · pandas · matplotlib/seaborn · Flask · Docker · GCP Cloud Run · GitHub Actions

---

## Running Locally

### With Docker (recommended)
```bash
docker compose up --build
# → open http://localhost:8080
```

### Without Docker (dev mode)
```bash
pip install -r requirements.txt
python analysis/generate_all.py      # pre-generates charts + JSON
python web/app.py                    # starts Flask dev server on :5000
```

---

## Project Structure

```
marketing-case-study-mojtaba/
├── data/
│   └── data.xlsx                  # Raw dataset (bundled into container)
├── analysis/
│   ├── 00_data_loader.py          # Shared data loading + computed columns
│   ├── 01_executive_summary.py    # Q1: Executive Summary
│   ├── 02_recommendations.py      # Q2: Recommendations & Visualizations
│   ├── 03_budget_allocation.py    # Q3: Budget Allocation Hypotheses
│   ├── 04_patterns_anomalies.py   # Q4: Key Patterns & Anomalies
│   ├── 05_data_gaps.py            # Q5: Data Gaps & Additional Inputs
│   └── generate_all.py            # Orchestrator — run this to regenerate everything
├── output/                        # Auto-generated (not in git)
│   ├── charts/                    # PNG chart files
│   └── data/                      # JSON output per question
├── web/
│   ├── app.py                     # Flask application
│   ├── templates/index.html       # Single-page branded UI
│   └── static/
│       ├── css/style.css          # Brand colors, typography, layout
│       └── js/app.js              # Accordion, lightbox, download handlers
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .github/workflows/deploy.yml   # Auto-deploy to Cloud Run on push to main
└── README.md
```

---

## Deployment

### Prerequisites (one-time GCP setup)
```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com
```

Create a Service Account with roles:
- `roles/run.admin`
- `roles/storage.admin`
- `roles/iam.serviceAccountUser`

Add to GitHub repository secrets:
- `GCP_PROJECT_ID` — your GCP project ID
- `GCP_SA_KEY` — JSON key of the Service Account

### Deploy
Push to `main` → GitHub Actions builds the Docker image, pushes to GCR, deploys to Cloud Run.

---

## Key Data Assumptions

- **UNKNOWN market/channel rows** are excluded from main analysis but included in the data gaps section.
- **Null conversions** (~62% of rows): only rows with `Conversion Channel 1 = Paid` or rows with tracked conversion funnels have conversion/revenue data. This is expected by dataset design.
- **Revenue attribution**: Invoice Date used for all ROAS calculations (confirmed payments only). Create Date is retained in the dataset for reference but not used in any metric.
- **ROAS** = New Revenue (Invoice Date) / Marketing Spendings; rows with 0 spend are excluded from ROAS calculation.
- **Cost per Subscriber** = Marketing Spendings / Subscriber count (where spend > 0).

---

## Privacy Statement

This solution is fully containerized. All data analysis runs inside the Docker container at
build time. No raw data is exposed via web routes at runtime. AI coding agents processed
only the data schema and statistical summaries — the raw dataset was never transmitted
outside the container environment — ensuring 100% data privacy.
