"""
3_post_hate_evaluation.py
─────────────────────────
Calculates hate impact KPIs from the DataFrame
produced by the previous pipeline step.

Impact score formula:
    impact_score = confidence × (likesCount + 1)
    The +1 ensures a minimum weight even for comments with 0 likes,
    based on the AI confidence score alone.

KPIs aggregated per category:
    impatto_totale = Σ impact_score
    impatto_medio  = impatto_totale / n_commenti

Standalone usage:
    python3 3_post_hate_evaluation.py analisi_odio_con_consenso.csv

Module usage:
    from 3_post_hate_evaluation import run
    stats = run(df)   # df: pd.DataFrame → list[dict]
"""

import sys

import pandas as pd


# ── Configuration ─────────────────────────────────────────────────────────────

ALL_CATEGORIES = ["ACCEPTABLE", "INAPPROPRIATE", "OFFENSIVE", "VIOLENT"]


# ── Core ──────────────────────────────────────────────────────────────────────

def run(df: pd.DataFrame) -> list:
    """
    Calculates impact KPIs per category.

    Args:
        df: DataFrame with columns categoria, confidenza, likesCount, text

    Returns:
        List of dicts ordered by ALL_CATEGORIES, with all 4 categories
        always present (zero values for categories absent in the post).
    """
    df = df.copy()

    # Impact score formula: confidence × (likes + 1)
    # The +1 ensures a minimum weight even for comments with 0 likes.
    df["impact_score"] = df["confidenza"] * (df["likesCount"] + 1)

    statistiche = df.groupby("categoria").agg(
        n_commenti    =("text",         "count"),
        totale_likes  =("likesCount",   "sum"),
        impatto_totale=("impact_score", "sum"),
    )

    statistiche["impatto_medio"] = (
        statistiche["impatto_totale"] / statistiche["n_commenti"]
    )

    statistiche = statistiche.sort_values("impatto_totale", ascending=False)

    return _ensure_all_categories(statistiche)


def _ensure_all_categories(df: pd.DataFrame) -> list:
    """
    Ensures all 4 categories are present in the result,
    inserting zero values for categories absent in the analysed post.
    """
    index = df.to_dict("index")
    result = []

    for cat in ALL_CATEGORIES:
        if cat in index:
            row = index[cat]
            result.append({
                "categoria":      cat,
                "n_commenti":     int(row["n_commenti"]),
                "totale_likes":   int(row["totale_likes"]),
                "impatto_totale": round(float(row["impatto_totale"]), 4),
                "impatto_medio":  round(float(row["impatto_medio"]), 4),
            })
        else:
            result.append({
                "categoria":      cat,
                "n_commenti":     0,
                "totale_likes":   0,
                "impatto_totale": 0.0,
                "impatto_medio":  0.0,
            })

    return result


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 3_post_hate_evaluation.py <analysis.csv>")
        sys.exit(1)

    df = pd.read_csv(sys.argv[1])
    stats = run(df)

    print("\n" + "=" * 40)
    print("📊 HATE SPEECH BAROMETER — FINAL REPORT")
    print("=" * 40)
    for row in stats:
        print(
            f"{row['categoria']:15} | "
            f"comments: {row['n_commenti']:3} | "
            f"total impact: {row['impatto_totale']:8.2f} | "
            f"avg impact: {row['impatto_medio']:.4f}"
        )
    print("=" * 40)
