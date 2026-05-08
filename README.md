# Marketing Campaign Analysis

A data analysis case study presenting 2024 marketing campaign insights to the CEO of the Company —
a subscription-based audio content platform. Built as a fully containerized, branded web application.

## Live Demo

Deployed on GCP Cloud Run. URL available after first deployment (see CI/CD setup below).

## Quick Start

```bash
git clone https://github.com/<your-username>/marketing-case-study-mojtaba.git
cd marketing-case-study-mojtaba
docker compose up --build
# → open http://localhost:8080
```

## What It Answers

| # | Question |
|---|----------|
| 1 | **Executive Summary** — Key findings and top recommendations |
| 2 | **Recommendations & Visualizations** — Actionable steps with supporting charts |
| 3 | **Budget Allocation Hypotheses** — Where to increase or decrease spend |
| 4 | **Key Patterns & Anomalies** — Trends, outliers, and implications |
| 5 | **Data Gaps & Additional Inputs** — What data would sharpen the analysis |

## CI/CD Setup (GitHub Actions → Cloud Run)

1. Enable GCP APIs:
   ```bash
   gcloud services enable run.googleapis.com containerregistry.googleapis.com
   ```

2. Create a Service Account with roles `run.admin`, `storage.admin`, `iam.serviceAccountUser`.
   Download its JSON key.

3. Add GitHub repository secrets:
   - `GCP_PROJECT_ID` — your GCP project ID
   - `GCP_SA_KEY` — contents of the JSON key file

4. Push to `main` — GitHub Actions handles the rest.

## Privacy

Since this analysis involves sensitive subscriber and revenue data, the solution is fully
containerized. All data processing occurs inside the Docker container at build time.
No raw data is exposed via web routes, and AI coding agents had zero access to the raw
dataset outside the container environment — ensuring 100% data privacy.

## Tech Stack

- **Analysis:** Python, pandas, matplotlib, seaborn
- **Web:** Flask, HTML/CSS/JS (branded)
- **Container:** Docker
- **Hosting:** GCP Cloud Run
- **CI/CD:** GitHub Actions
