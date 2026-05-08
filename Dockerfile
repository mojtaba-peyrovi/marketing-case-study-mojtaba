FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/ data/
COPY analysis/ analysis/
COPY web/ web/

# Pre-generate all charts and JSON at build time
# Raw data never touches the network at runtime
RUN python analysis/generate_all.py

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "web.app:app"]
