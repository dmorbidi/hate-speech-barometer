"""
2_comments_hate_analysis.py
───────────────────────────
Classifies Facebook comments using the HuggingFace model
IMSyPP/hate_speech_it, assigning each comment a category
and a confidence score.

Standalone usage:
    python3 2_comments_hate_analysis.py <input.json>

Module usage:
    from 2_comments_hate_analysis import run
    df = run(comments)   # comments: list[dict] → pd.DataFrame
"""

import json
import sys
import os
from pathlib import Path
import pandas as pd
from transformers import pipeline

# Persistent cache for the HuggingFace model.
# Points to scripts/.cache/ — works both on Ubuntu and inside the Devilbox container.
os.environ["TRANSFORMERS_CACHE"] = str(Path(__file__).parent / ".cache")

# ── Configuration ─────────────────────────────────────────────────────────────

MODEL_ID = "IMSyPP/hate_speech_it"

LABEL_MAP = {
    "LABEL_0": "ACCEPTABLE",
    "LABEL_1": "INAPPROPRIATE",
    "LABEL_2": "OFFENSIVE",
    "LABEL_3": "VIOLENT",
}


# ── Core ──────────────────────────────────────────────────────────────────────

def run(comments: list) -> pd.DataFrame:
    """
    Classifies a list of Facebook comments.

    Args:
        comments: list of dicts with keys postTitle, text, likesCount, facebookUrl

    Returns:
        DataFrame with original columns plus 'categoria' (category) and 'confidenza' (precision)
    """
    df = pd.DataFrame(comments)

    # Convert likes to integers.
    # errors='coerce' turns any non-numeric values into NaN, then fills with 0.
    df["likesCount"] = (
        pd.to_numeric(df["likesCount"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    print("Loading model...", file=sys.stderr)
    hate_classifier = pipeline(
        "text-classification",
        model=MODEL_ID,
        truncation=True,
    )

    print("Classifying comments...", file=sys.stderr)

    def analizza(testo):
        # res = hate_classifier(str(testo))[0]
        res = hate_classifier(str(testo), truncation=True, max_length=512)[0]
        return pd.Series([LABEL_MAP.get(res["label"]), res["score"]])

    df[["categoria", "confidenza"]] = df["text"].apply(analizza)

    return df


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 2_comments_hate_analysis.py <input.json>")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        comments = json.load(f)

    df = run(comments)
    print(df.to_csv(index=False))
