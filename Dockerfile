FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/ data/
COPY analysis/ analysis/
COPY tests/ tests/
COPY web/ web/

# Step 1: run metric unit tests — build fails here if any formula is wrong
RUN python tests/test_metrics.py

# Step 2: validate raw data — build fails here if data is corrupt or malformed
# Step 3: run all analysis scripts and generate charts + JSON
RUN python analysis/generate_all.py

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "web.app:app"]
