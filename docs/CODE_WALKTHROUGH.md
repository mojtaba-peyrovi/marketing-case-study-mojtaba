# Code Walkthrough

A step-by-step guide to reading the codebase in the order it was built and the order it executes.
Each section explains what the file does, why it exists, and what to look for when reading it.

---

## Step 1 — Understand the data

### `data/data.xlsx`
The raw source dataset. 1,152 rows × 17 columns. Open it in Excel before reading any code.

Key things to notice:
- Each row is one **channel × month** combination (e.g. Facebook/Instagram Ads in German market, January)
- There are three channel hierarchy columns: `Conversion Channel 1` (Paid / Non-Paid), `Conversion Channel 2` (e.g. Influencer, Performance Marketing), `Conversion Channel 3` (the specific channel, e.g. Influencer Instagram)
- `Monthly Conversions`, `Yearly Conversions`, and revenue columns are **null for ~62% of rows** — only rows with tracked conversion data have these filled in
- `Marketing Spendings` is **0 for all non-paid channels** (organic, word-of-mouth, etc.)
- There are UNKNOWN values in market and channel columns (~25% of rows) — these represent unattributed traffic

### `docs/instructions.pdf`
The original brief from the Company. Five questions the analysis must answer. Read this first to understand what every subsequent script is trying to produce.

---

## Step 2 — Data pipeline

These four files run in sequence every time the Docker image is built.

### `analysis/data_loader.py`

**What it does:** Loads `data/data.xlsx`, cleans it, and adds computed columns that every other script uses.

**Key things to read:**
- The `REQUIRED_COLUMNS` list at the top — shows exactly which columns are expected
- The `load_data()` function — follow it line by line to see every transformation
- The `paid_conversions` column: `Monthly Paid Conversions + Yearly Paid Conversions` — this is the denominator in CAC. Both plan types (monthly and yearly) are summed because both represent real paying customers; CAC should reflect the cost to acquire any paying subscriber regardless of which plan they chose
- The coupon clamping block: one known anomaly in the real data (PR / English / February has `Share Coupon Used = 1.3333`, which is impossible for a ratio). The value is clamped to 1.0 here and flagged for the data team in `validate_data.py`
- Returns two DataFrames: `df_full` (all 1,152 rows) and `df_conv` (the 434 rows that have non-null conversion data)

### `analysis/validate_data.py`

**What it does:** Runs 8 data quality checks against `df_full` before any analysis starts. If a hard check fails, it prints a plain-English error message and the Docker build stops — a broken dataset can never silently produce wrong numbers.

**Key things to read:**
- The `DataValidationError` exception class — this is what gets raised on failure
- Each numbered check and its error message — the messages are written to be forwarded directly to a data team without interpretation
- The distinction between **hard errors** (build stops) and **soft warnings** (build continues, row flagged): values between 1.0 and 1.5 in coupon columns are warned but not fatal; values outside that range are fatal
- The `_fail()` helper at the bottom — formats the error block that prints to the CI/CD log

### `analysis/dashboard_data.py`

**What it does:** The main aggregation script. Computes every metric that appears in the UI and writes them all to `output/data/dashboard.json`.

**Key things to read:**
- The `CAC` calculation: `spend / paid_conversions` — uses the combined Monthly + Yearly Paid column from `data_loader.py`
- The `ROAS` calculation: `New Revenue Invoice Date / Marketing Spendings` — uses confirmed payments only. Create Date would include trial starters who never pay, overstating ROAS
- The `trial_to_paid` calculation: `Yearly Paid Conversions / Yearly Conversions` — measures what share of free trials converted to paying, per channel. This is a quality signal that CAC alone cannot capture
- The `_verdict()` function — classification logic that assigns Scale / Reduce / Kill / Paused / Monitor to each channel based on its CAC, ROAS, and trial-to-paid rate
- The market loop — aggregates the same metrics (spend, CAC, ROAS, trial-to-paid, ARPU) per market (German, French, English)

### `analysis/generate_all.py`

**What it does:** The orchestrator. Imports and runs every analysis script in the correct sequence. This is the single command Docker calls at build time.

**Key things to read:**
- The import of `validate` from `validate_data.py` — validation runs before any script is called
- The `_load_script()` helper — uses Python's `importlib` to import the numbered scripts (`01_`, `02_`, etc.) because Python cannot import modules whose names start with a digit
- The sequence: load data → validate → run Q1–Q5 scripts → run dashboard_data → done

---

## Step 3 — Supporting analysis scripts

Each script answers one of the five questions from the brief. They all follow the same pattern: receive `df_full` and `df_conv` from the orchestrator, compute findings, write a JSON file to `output/data/`, and (for Q2–Q4) save chart images to `output/charts/`.

| File | Question answered | Output |
|------|------------------|--------|
| `analysis/01_executive_summary.py` | Q1 — Executive Summary | `output/data/executive_summary.json` |
| `analysis/02_recommendations.py` | Q2 — Recommendations & Visualizations | `output/data/recommendations.json` + 4 PNG charts |
| `analysis/03_budget_allocation.py` | Q3 — Budget Allocation Hypotheses | `output/data/budget_allocation.json` + 2 PNG charts |
| `analysis/04_patterns_anomalies.py` | Q4 — Key Patterns & Anomalies | `output/data/patterns_anomalies.json` + 3 PNG charts |
| `analysis/05_data_gaps.py` | Q5 — Data Gaps & Additional Inputs | `output/data/data_gaps.json` |

**Key things to read in any of these scripts:**
- The module-level docstring at the top — explains the methodology and assumptions for that question
- The `run(df_full, df_conv)` function signature — this is what `generate_all.py` calls
- The `output` dictionary at the bottom of each `run()` — this is exactly what ends up in the JSON file, and therefore what the UI renders

---

## Step 4 — Tests

### `tests/test_metrics.py`

**What it does:** 11 unit tests that verify every metric formula. Uses a small hand-crafted DataFrame with known values so each expected answer can be verified by mental arithmetic.

**Key things to read:**
- `MOCK_DF` at the top — two rows (one paid channel, one non-paid). All expected test outputs are derived from these numbers
- Each `test_` function — the assertion comment explains the expected value and how to derive it by hand
- `test_cac_zero_spend_returns_nan` and `test_roas_zero_spend_is_undefined` — confirm that non-paid channels correctly produce NaN (undefined), not zero, for cost and return metrics
- `test_trial_to_paid_max_one` — confirms a logical invariant: paid conversions can never exceed total conversions
- The `__main__` block at the bottom — runs all tests without needing pytest; output is plain pass/fail per test

---

## Step 5 — Web layer

### `web/app.py`

**What it does:** A 40-line Flask server. Loads pre-computed JSON files and serves them to the template. Nothing is computed at runtime.

**Key things to read:**
- `_load()` helper — reads a JSON file from `output/data/`; returns an empty dict if the file doesn't exist (safe fallback)
- The `/` route — loads `dashboard.json` and `data_gaps.json`, passes them as template variables
- The `/download/chart/<filename>` route — serves chart PNG files as downloadable attachments

### `web/templates/index.html`

**What it does:** The full UI. A Jinja2 template that renders all five question sections using data injected by `app.py`.

**Key things to read:**
- The Question Navigator near the top — the five anchor links map directly to the five `<section id="q1">` through `<section id="q5">` blocks below
- Each `q-banner` div — contains the exact question text from the brief, making the mapping explicit
- The Jinja2 expressions like `{{ d.kpis.total_spend }}` — `d` is `dashboard.json`, `gaps` is `data_gaps.json`; all numbers on the page come from these two files
- The channel card loop (`{% for c in d.channels %}`) — the `.good` / `.bad` CSS classes are applied conditionally in the template based on metric thresholds
- The metric definitions section near the bottom — six cards explaining every formula used, with worked examples from the real data
- `window.DASHBOARD = {{ dashboard_json|safe }}` — embeds the full JSON into the page for Chart.js to consume client-side

### `web/static/css/style.css`

**What it does:** All styling. Based on the Company brand palette.

**Key things to read:**
- The `:root` block at the top — all colours as CSS variables (`--coral`, `--lavender`, `--ink`, etc.)
- `.metric-val.good` and `.metric-val.bad` — the two classes used throughout for green/red metric colouring
- `.q-banner` — the dark question header that appears at the top of each section
- `.metric-def-card` and `.metric-def-formula` — the metric definition cards at the bottom of the page

### `web/static/js/app.js`

**What it does:** Reads `window.DASHBOARD` (embedded JSON) and initialises three Chart.js charts.

**Key things to read:**
- The three canvas IDs: `efficiencyChart`, `metaChart`, `t2pChart` — match the `<canvas>` elements in the template
- The colour mapping in `t2pChart` — `paid_good` (green), `paid` (coral), `paid_warn` (amber), `organic` (purple) — set in `dashboard_data.py`'s `_verdict` logic

---

## Step 6 — Infrastructure

### `Dockerfile`

**What it does:** Defines the container. Three build steps, in this order:

```
1. pip install -r requirements.txt
2. python tests/test_metrics.py          ← build fails if any formula is wrong
3. python analysis/generate_all.py       ← validates data, then generates all outputs
```

Only `web/` and `output/` (generated in step 3) are available at runtime. The raw `data/` directory is present during build but its contents are not reachable via any web route.

### `.github/workflows/deploy.yml`

**What it does:** Full CI/CD pipeline triggered on every push to `main`.

**Key things to read:**
- The `Download data from GCS` step — fetches `data.xlsx` from a private Google Cloud Storage bucket (`gs://marketing-case-study-mojtaba-data`). The file is never stored in git; the GCS bucket is private and only the service account can read it
- The two GitHub secrets (`GCP_PROJECT_ID`, `GCP_SA_KEY`) — the only credentials needed; defined in the repo settings, not in any file
- The `gcloud run deploy` command — `--allow-unauthenticated` makes the URL publicly accessible; `--memory 512Mi` is sufficient because all heavy computation happens at build time

### `CLAUDE.md`

**What it does:** Project guide for anyone continuing development. Covers: how to run locally, key data assumptions, the full file structure, and deployment instructions.

---

## How it all connects

```
data.xlsx  ──►  data_loader.py  ──►  validate_data.py  ──►  dashboard_data.py
                                                         ──►  01_ through 05_ scripts
                                                         ──►  output/data/*.json
                                                              output/charts/*.png
                                                                    │
                                                               web/app.py
                                                                    │
                                                         web/templates/index.html
                                                         web/static/css/style.css
                                                         web/static/js/app.js
```

The key architectural decision: **all computation happens at build time**. At runtime the Flask server is just a file server — it reads pre-computed JSON and sends it to the browser. This is why the raw data file never needs to be accessible at runtime, and why the app starts instantly with no database.
