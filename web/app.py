"""
Flask application — serves the Marketing Campaign Analysis UI.

All analysis is pre-computed at Docker build time (analysis/generate_all.py).
At runtime this app only serves static JSON + chart assets — no raw data is exposed.
"""

import json
import os

from flask import Flask, abort, render_template, send_from_directory

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
    context = {
        "q1": _load("executive_summary.json"),
        "q2": _load("recommendations.json"),
        "q3": _load("budget_allocation.json"),
        "q4": _load("patterns_anomalies.json"),
        "q5": _load("data_gaps.json"),
    }
    return render_template("index.html", **context)


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
