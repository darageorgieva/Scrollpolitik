import re
import pandas as pd


def naive_split_sentences(text):
    parts = re.compile(r"[.!?]+(?:\s+|$)").split(text.strip())
    return [p.strip() for p in parts if p.strip()]

def analyze_sentence_split_agreement_naive_split(df, text_col="text", ref_col="NSentences",
                                      undercount_classify_cap=5, verbose=True):
    """
    Compares our naive [.!?]-based sentence count against the file's NSentences
    column. This is the check behind the numbers 59.7% exact match, 0.99
    correlation.

    It is a sanity check and it needs only the CSV. Idea is that in order to
    talk about comparison with the paper reported mean sentiment we need to
    ensure methodology is exact.

    Returns a dict of stats; prints a short report if verbose=True.
    """
    naive_counts = df[text_col].fillna("").apply(lambda t: len(naive_split_sentences(t)))
    notna_row = df[ref_col].notna()

    n = int(notna_row.sum())
    corr = df.loc[notna_row, ref_col].corr(naive_counts[notna_row])
    exact_match_rate = (df.loc[notna_row, ref_col] == naive_counts[notna_row]).mean()
    undercount_mask = notna_row & (naive_counts == 1) & (df[ref_col] >= undercount_classify_cap)

    stats = {
        "n_rows": n,
        "correlation": float(corr),
        "exact_match_rate": float(exact_match_rate),
        "undercount_subset_rows": int(undercount_mask.sum()),
        "undercount_subset_share": float(undercount_mask.mean()),
    }

    if verbose:
        print(f"naive-split vs {ref_col}  (n={n:,})")
        print(" ")
        print(f"  correlation:       {stats['correlation']:.3f}")
        print(f"  exact match rate:  {stats['exact_match_rate']:.1%}")
        print(f"  undercount subset: {stats['undercount_subset_rows']:,} rows "
              f"({stats['undercount_subset_share']:.2%}) where naive split count = 1 "
              f"but {ref_col} >= {undercount_classify_cap}")

    return stats


def main():
    df = pd.read_csv("data/df_tiktok.csv")
    analyze_sentence_split_agreement_naive_split(df)


if __name__ == "__main__":
    main()
