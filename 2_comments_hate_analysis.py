"""
2_comments_hate_analysis.py
───────────────────────────
Classifica i commenti Facebook con il modello HuggingFace
IMSyPP/hate_speech_it, assegnando a ciascuno una categoria
e un livello di confidenza.

Utilizzo standalone:
    python3 2_comments_hate_analysis.py estrazione_amnesty.json

Utilizzo come modulo:
    from 2_comments_hate_analysis import run
    df = run(comments)   # comments: list[dict] → pd.DataFrame
"""

import json
import sys

import pandas as pd
from transformers import pipeline


# ── Configurazione ────────────────────────────────────────────────────────────

MODEL_ID = "IMSyPP/hate_speech_it"

MAPPING_UFFICIALE = {
    "LABEL_0": "ACCEPTABLE",
    "LABEL_1": "INAPPROPRIATE",
    "LABEL_2": "OFFENSIVE",
    "LABEL_3": "VIOLENT",
}


# ── Core ──────────────────────────────────────────────────────────────────────

def run(comments: list) -> pd.DataFrame:
    """
    Classifica una lista di commenti Facebook.

    Args:
        comments: lista di dict con chiavi postTitle, text, likesCount, facebookUrl

    Returns:
        DataFrame con colonne originali più 'categoria' e 'confidenza'
    """
    df = pd.DataFrame(comments)

    # Convertiamo i likes in numeri interi
    # errors='coerce' trasforma eventuali testi strani in NaN, poi a 0
    df["likesCount"] = (
        pd.to_numeric(df["likesCount"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    print("Caricamento modello...", file=sys.stderr)
    hate_classifier = pipeline(
        "text-classification",
        model=MODEL_ID,
        truncation=True,
    )

    print("Analisi in corso...", file=sys.stderr)

    def analizza(testo):
        res = hate_classifier(str(testo))[0]
        return pd.Series([MAPPING_UFFICIALE.get(res["label"]), res["score"]])

    df[["categoria", "confidenza"]] = df["text"].apply(analizza)

    return df


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 2_comments_hate_analysis.py <input.json>")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        comments = json.load(f)

    df = run(comments)
    print(df.to_csv(index=False))
