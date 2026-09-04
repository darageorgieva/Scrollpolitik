"""
Sentiment annotation + validation against Solovev et al. (2026) (Methods, Sect 3.2), OSF df_tiktok.csv.

Reproduces the paper's sentiment pipeline (Methods, Sect 3.2) the
model tabularisai/multilingual-sentiment-analysis: score each sentence into
one of five classes, average to a video-level continuous score, then bin at
+/-0.5 into negative / neutral / positive.

Sentence splitting: NSentences in the OSF file can't be reliably reconstructed
from the flattened `text` column. Splitting `text` naively on [.!?] and
counting the pieces matches the file's NSentences exactly on 59.7% of the
25,292 rows, and the two are correlated at 0.993 across the full file. 

Usage (run from inside src/):
    python3 sentiment-script.py --data ../data/df_tiktok.csv --out ../data/df_tiktok_scored.csv
    python3 sentiment-script.py --data ../data/df_tiktok.csv --limit 200      # smoke test
    python3 sentiment-script.py --data ../data/df_tiktok.csv --device cuda    # GPU

Requires: pip install transformers torch pandas
Model download needs network access to huggingface.co.
"""
import argparse
import re
from transformers import pipeline
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

SCORE_MAP = {
    "Very Negative": -2, "Negative": -1, "Neutral": 0,
    "Positive": 1, "Very Positive": 2,
}


def split_sentences(text):
    parts = re.compile(r"[.!?]+(?:\s+|$)").split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def categorize(score):
    """Paper's binning rule: negative < -0.5 < neutral < 0.5 < positive."""
    if pd.isna(score):
        return None
    if score < -0.5:
        return "Negative"
    if score > 0.5:
        return "Positive"
    return "Neutral"


def load_model(device, max_length=256):
    os.getenv("HF_TOKEN")
    return pipeline(
        "text-classification",
        model="tabularisai/multilingual-sentiment-analysis",
        device=device,
        truncation=True,
        max_length=max_length,
        token=os.getenv("HF_TOKEN")
    )


def score_dataframe(df, device, text_col="text", batch_size=64):
    # owners is a parallel list remembering which row (by position, 0-indexed)
    # each sentence came from, so per-sentence scores can be folded back into
    # a per-video average below.
    sentences, owners = [], []
    for i, t in enumerate(df[text_col].fillna("")):
        for s in split_sentences(t):
            sentences.append(s)
            owners.append(i)

    df = df.copy()
    if not sentences:
        df["our_sentiment_score"] = pd.NA
        df["our_sentiment"] = None
        return df

    pipe = load_model(device)
    preds = pipe(sentences, batch_size=batch_size)
    scores = [SCORE_MAP.get(p["label"], 0) for p in preds]

    agg = (
        pd.DataFrame({"video_idx": owners, "score": scores})
        .groupby("video_idx")["score"]
        .mean()
    )
    # owners holds positions (0..len(df)-1), not df's index labels, so align
    # by position here rather than via df.index.map - otherwise a df with a
    # non-default index (e.g. filtered rows) would get scores assigned to the
    # wrong rows.
    df["our_sentiment_score"] = agg.reindex(range(len(df))).to_numpy()
    df["our_sentiment"] = df["our_sentiment_score"].apply(categorize)
    return df


def compare_to_reference(df, ref_col="MeanSentiment"):
    agreement = (df["our_sentiment"] == df[ref_col]).mean()
    confusion = pd.crosstab(
        df[ref_col], df["our_sentiment"],
        rownames=["paper (MeanSentiment)"], colnames=["ours"], dropna=False,
    )
    return agreement, confusion, len(df)

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="sample N videos for a quick run instead of the full file")
    ap.add_argument("--device", default="cpu", help="'cpu', 'cuda', or a device index")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--seed", type=int, default=42)

    args = ap.parse_args()

    df = pd.read_csv(args.data)
    if args.limit:
        df = df.sample(args.limit, random_state=args.seed).reset_index(drop=True)
        print(f"sampled {args.limit} videos for a quick run")
    print(f"loaded {len(df):,} videos")


    print("loading tabularisai/multilingual-sentiment-analysis ...")
    df = score_dataframe(df, args.device, batch_size=args.batch_size)

    result = compare_to_reference(df)

    agreement, confusion, n = result
    print(f"\nagreement with MeanSentiment: {agreement:.1%}  (n={n:,})")
    print(confusion.to_string())


    out_path = args.out or args.data.rsplit(".", 1)[0] + "_scored.csv"
    df.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()