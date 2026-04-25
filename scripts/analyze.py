#!/usr/bin/env python3
"""
analyze.py
──────────
Entry point chiamato da WordPress via exec().
Catena i 3 script della pipeline in memoria (nessun file su disco)
e stampa il risultato finale come JSON su stdout.

Uso:
    python3 analyze.py <facebook_post_url>

Variabili d'ambiente:
    APIFY_TOKEN    Token Apify (richiesto in modalità produzione)
    HSA_TEST_MODE  Impostare a "1" per usare il file JSON locale
    HSA_TEST_FILE  Percorso del file JSON di test
                   (default: scripts/estrazione_amnesty.json)

IMPORTANTE: questo script stampa SOLO JSON su stdout.
            Qualsiasi altro output va su stderr.
"""

import json
import sys
import importlib
from pathlib import Path

# Usa il Python del venv se disponibile
import os
SCRIPTS_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPTS_DIR / "venv/bin/python3"

if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    # Rilancia lo script usando il Python del venv
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

# Aggiunge la cartella scripts/ al path così Python trova i moduli
sys.path.insert(0, str(Path(__file__).parent))

scraping   = importlib.import_module("1_fb_comments_scraping")
analysis   = importlib.import_module("2_comments_hate_analysis")
evaluation = importlib.import_module("3_post_hate_evaluation")


def main() -> None:
    if len(sys.argv) < 2:
        _error("Uso: python3 analyze.py <facebook_post_url>")

    post_url = sys.argv[1]

    try:
        # Step 1 — recupera commenti (da Apify o da file locale)
        comments = scraping.run(post_url)

        if not comments:
            _error("Nessun commento trovato per questo post.")

        # Step 2 — classifica con HuggingFace
        df_classified = analysis.run(comments)

        # Step 3 — calcola KPI
        stats = evaluation.run(df_classified)

        # Output finale: JSON su stdout
        output = {
            "post_title": comments[0].get("postTitle", "") if comments else "",
            "post_url":   post_url,
            "stats":      stats,
        }

        print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        _error(str(e))


def _error(message: str) -> None:
    """Stampa un JSON di errore su stdout ed esce con codice 1."""
    print(json.dumps({"error": message}, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
