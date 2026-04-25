"""
3_post_hate_evaluation.py
─────────────────────────
Calcola i KPI di impatto odio a partire dal DataFrame
classificato dallo step precedente.

Formula impact score:
    impact_score = confidenza × (likesCount + 1)
    Il +1 garantisce peso minimo anche ai commenti con 0 like,
    basato sulla certezza dell'AI.

KPI aggregati per categoria:
    impatto_totale = Σ impact_score
    impatto_medio  = impatto_totale / n_commenti

Utilizzo standalone:
    python3 3_post_hate_evaluation.py analisi_odio_con_consenso.csv

Utilizzo come modulo:
    from 3_post_hate_evaluation import run
    stats = run(df)   # df: pd.DataFrame → list[dict]
"""

import sys

import pandas as pd


# ── Configurazione ────────────────────────────────────────────────────────────

ALL_CATEGORIES = ["ACCEPTABLE", "INAPPROPRIATE", "OFFENSIVE", "VIOLENT"]


# ── Core ──────────────────────────────────────────────────────────────────────

def run(df: pd.DataFrame) -> list:
    """
    Calcola i KPI di impatto per categoria.

    Args:
        df: DataFrame con colonne categoria, confidenza, likesCount, text

    Returns:
        Lista di dict ordinata per ALL_CATEGORIES, con tutte e 4
        le categorie sempre presenti (valori zero se assenti).
    """
    df = df.copy()

    # Formula originale: confidenza × (likes + 1)
    # Il +1 assicura peso minimo anche ai commenti con 0 like
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
    Garantisce che tutte e 4 le categorie siano presenti nel risultato,
    inserendo valori zero per quelle assenti nel post analizzato.
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
        print("Uso: python3 3_post_hate_evaluation.py <analisi.csv>")
        sys.exit(1)

    df = pd.read_csv(sys.argv[1])
    stats = run(df)

    print("\n" + "=" * 40)
    print("📊 REPORT FINALE: TEMPERATURA DELL'ODIO")
    print("=" * 40)
    for row in stats:
        print(
            f"{row['categoria']:15} | "
            f"commenti: {row['n_commenti']:3} | "
            f"impatto totale: {row['impatto_totale']:8.2f} | "
            f"impatto medio: {row['impatto_medio']:.4f}"
        )
    print("=" * 40)
