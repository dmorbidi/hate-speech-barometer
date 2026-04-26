"""
1_fb_comments_scraping.py
─────────────────────────
Fetches comments from a Facebook post via Apify.

TEST MODE:  set HSB_TEST_MODE=1
            Reads a local JSON file instead of calling Apify.

PRODUCTION MODE:  requires the APIFY_TOKEN environment variable.
                  See README for configuration instructions.

Standalone usage:
    python3 1_fb_comments_scraping.py <facebook_post_url>

Module usage:
    from 1_fb_comments_scraping import run
    comments = run(url)   # → list[dict]
"""

import json
import os
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

APIFY_ACTOR_ID  = "apify/facebook-comments-scraper"
RESULTS_LIMIT   = 50

# Default test file path — used only when running this script standalone
# (i.e. without HSB_TEST_FILE environment variable set).
# In production, HSB_TEST_FILE in wp-config.php takes precedence.
# Ensure this file is anonymized before committing to any public repository.
DEFAULT_TEST_FILE = Path(__file__).parent / "anonymized_dataset_sample.json"


# ── Core ──────────────────────────────────────────────────────────────────────

def run(post_url: str) -> list:
    """
    Fetches comments from the given Facebook post.

    In test mode (HSB_TEST_MODE=1) reads from a local file.
    In production mode calls the Apify API.

    Returns:
        List of dicts with keys: postTitle, text, likesCount, facebookUrl
    """
    if os.getenv("HSB_TEST_MODE") == "1":
        return _load_from_file()
    return _fetch_from_apify(post_url)


def _load_from_file() -> list:
    """Loads comments from a local JSON file (test mode)."""
    test_file = Path(os.getenv("HSB_TEST_FILE", DEFAULT_TEST_FILE))

    if not test_file.exists():
        raise FileNotFoundError(
            f"Test file not found: {test_file}\n"
            f"Set HSB_TEST_FILE to the correct path."
        )

    with open(test_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Test mode: loaded {len(data)} comments from {test_file}", file=sys.stderr)
    return data


def _fetch_from_apify(post_url: str) -> list:
    """Calls the Apify actor and returns the comments (production mode)."""
    from apify_client import ApifyClient

    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise EnvironmentError(
            "APIFY_TOKEN environment variable is not set.\n"
            "See README for configuration instructions."
        )

    client = ApifyClient(token)

    run_input = {
        "startUrls":             [{"url": post_url}],
        "resultsLimit":          RESULTS_LIMIT,
        "includeNestedComments": True,
        "viewOption":            "RANKED_UNFILTERED",
    }

    print("Launching Apify scraper... (this may take a minute)", file=sys.stderr)

    actor_run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)
    items = client.dataset(actor_run["defaultDatasetId"]).list_items().items

    print(f"Scraping complete. Run ID: {actor_run['id']}", file=sys.stderr)
    return items


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 1_fb_comments_scraping.py <facebook_post_url>")
        sys.exit(1)

    comments = run(sys.argv[1])
    print(json.dumps(comments, ensure_ascii=False, indent=2))
