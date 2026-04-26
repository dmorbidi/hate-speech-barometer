#!/usr/bin/env python3
"""
analyze.py
──────────
Entry point called by WordPress via exec().
Chains the 3 pipeline scripts in memory (no files written to disk)
and prints the final result as JSON to stdout.

Usage:
    python3 analyze.py <facebook_post_url>

Environment variables:
    APIFY_TOKEN    Apify token (required in production mode)
    HSB_TEST_MODE  Set to "1" to use a local JSON file instead of calling Apify
    HSB_TEST_FILE  Path to the local test JSON file
                   (default: scripts/anonymized_dataset_sample.json)

IMPORTANT: this script prints ONLY JSON to stdout.
           Any other output must go to stderr.
"""

import json
import sys
import importlib
from pathlib import Path

# ── Add venv packages to sys.path ─────────────────────────────────────────────
# Works both on Ubuntu and inside the Devilbox container because it uses
# paths relative to this file, not absolute venv paths.
SCRIPTS_DIR = Path(__file__).parent
VENV_SITE_PACKAGES = SCRIPTS_DIR / "venv/lib"

if VENV_SITE_PACKAGES.exists():
    for py_dir in VENV_SITE_PACKAGES.iterdir():
        site_pkg = py_dir / "site-packages"
        if site_pkg.exists():
            sys.path.insert(0, str(site_pkg))
            break

# ── Add the scripts/ folder to sys.path so Python can find the modules ────────
sys.path.insert(0, str(SCRIPTS_DIR))

scraping   = importlib.import_module("1_fb_comments_scraping")
analysis   = importlib.import_module("2_comments_hate_analysis")
evaluation = importlib.import_module("3_post_hate_evaluation")


def main() -> None:
    if len(sys.argv) < 2:
        _error("Usage: python3 analyze.py <facebook_post_url>")

    post_url = sys.argv[1]

    try:
        # Step 1 — fetch comments (from Apify or local file)
        comments = scraping.run(post_url)

        if not comments:
            _error("No comments found for this post.")

        # Step 2 — classify with HuggingFace
        df_classified = analysis.run(comments)

        # Step 3 — calculate KPIs
        stats = evaluation.run(df_classified)

        # Final output: JSON to stdout
        output = {
            "post_title": comments[0].get("postTitle", "") if comments else "",
            "post_url":   post_url,
            "stats":      stats,
        }

        print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        _error(str(e))


def _error(message: str) -> None:
    """Print a JSON error to stdout and exit with code 1."""
    print(json.dumps({"error": message}, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
