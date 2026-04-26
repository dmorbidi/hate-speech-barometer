"""
1_fb_comments_scraping.py
─────────────────────────
Recupera i commenti di un post Facebook tramite Apify.

MODALITÀ TEST:  imposta HSB_TEST_MODE=1
                Legge il file JSON locale invece di chiamare Apify.

MODALITÀ PROD:  richiede la variabile d'ambiente APIFY_TOKEN.
                Vedere README per le istruzioni di configurazione.

Utilizzo standalone:
    python3 1_fb_comments_scraping.py <facebook_post_url>

Utilizzo come modulo:
    from 1_fb_comments_scraping import run
    comments = run(url)   # → list[dict]
"""

import json
import os
import sys
from pathlib import Path

# ── Configurazione ────────────────────────────────────────────────────────────

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
    Recupera i commenti del post Facebook indicato.

    In modalità test (HSB_TEST_MODE=1) legge da file locale.
    In modalità produzione chiama l'API Apify.

    Returns:
        Lista di dict con chiavi: postTitle, text, likesCount, facebookUrl
    """
    if os.getenv("HSB_TEST_MODE") == "1":
        return _load_from_file()
    return _fetch_from_apify(post_url)


def _load_from_file() -> list:
    """Carica i commenti dal file JSON locale (modalità test)."""
    test_file = Path(os.getenv("HSB_TEST_FILE", DEFAULT_TEST_FILE))

    if not test_file.exists():
        raise FileNotFoundError(
            f"File di test non trovato: {test_file}\n"
            f"Imposta HSB_TEST_FILE con il percorso corretto."
        )

    with open(test_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Modalità test: caricati {len(data)} commenti da {test_file}", file=sys.stderr)
    return data


def _fetch_from_apify(post_url: str) -> list:
    """Chiama l'actor Apify e restituisce i commenti (modalità produzione)."""
    from apify_client import ApifyClient

    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise EnvironmentError(
            "Variabile d'ambiente APIFY_TOKEN non impostata.\n"
            "Vedere README per le istruzioni di configurazione."
        )

    client = ApifyClient(token)

    run_input = {
        "startUrls":             [{"url": post_url}],
        "resultsLimit":          RESULTS_LIMIT,
        "includeNestedComments": True,
        "viewOption":            "RANKED_UNFILTERED",
    }

    print("Lancio dello scraper su Apify... (potrebbe volerci un minuto)", file=sys.stderr)

    actor_run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)
    items = client.dataset(actor_run["defaultDatasetId"]).list_items().items

    print(f"Scraping completato! ID Esecuzione: {actor_run['id']}", file=sys.stderr)
    return items


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 1_fb_comments_scraping.py <facebook_post_url>")
        sys.exit(1)

    comments = run(sys.argv[1])
    print(json.dumps(comments, ensure_ascii=False, indent=2))
