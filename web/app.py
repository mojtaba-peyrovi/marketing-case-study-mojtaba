"""
Flask application — serves the Marketing Performance Diagnostic.

All analysis is pre-computed at Docker build time (analysis/generate_all.py).
At runtime this app only serves pre-computed JSON + chart images.
No raw data is exposed via any web route.
"""

import json
import os

from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
DATA_DIR   = os.path.join(OUTPUT_DIR, "data")
CHART_DIR  = os.path.join(OUTPUT_DIR, "charts")


def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    dashboard = _load("dashboard.json")
    data_gaps = _load("data_gaps.json")
    return render_template(
        "index.html",
        d=dashboard,
        gaps=data_gaps,
        dashboard_json=json.dumps(dashboard),
    )


@app.route("/charts/<path:filename>")
def chart(filename):
    return send_from_directory(CHART_DIR, filename)


@app.route("/download/chart/<path:filename>")
def download_chart(filename):
    return send_from_directory(
        CHART_DIR, filename,
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/dashboard.json")
def api_dashboard():
    """Expose the pre-computed dashboard JSON for download / inspection."""
    return send_from_directory(DATA_DIR, "dashboard.json")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
