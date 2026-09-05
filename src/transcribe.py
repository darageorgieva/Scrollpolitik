"""
Video transcription Solovev et al. (2026) (Methods, Sect 3.1)

Reproduces the paper's video transcription method using the
openai/whisper model.

Prerequisites:
Requires data/video_metadata_media_type.csv" to be present,
which can be generated with: python determine_media_type.py

Remarks:
Will skip transcription for all media items where
media_type != video (as specified in
data/metadata_media_type.csv).

Usage:
python transcribe.py --metadat video_metadata_media_type.csv --out videos_transcribed.csv --model turbo --chkpt_itv 100
python transcribe.py --model tiny --limit 10

Requires: pip install torch, pandas, openai-whisper, static-ffmpeg

"""

import static_ffmpeg
static_ffmpeg.add_paths()#add ffmpeg binaries to PATH for current process (the system ffmpeg on hpc doesn't seem to work)
import argparse
import whisper
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser()

ap.add_argument("--metadat", default="video_metadata_media_type.csv")
ap.add_argument("--out", default="videos_transcribed.csv")
ap.add_argument("--limit", type=int, default=None,
                help="only transcribe the first N videos to test functionality")
ap.add_argument("--model", default="turbo",
                help="Available values: tiny, base, small, medium, large, turbo")
ap.add_argument("--chkpt_itv", type=int, default=100,
                help="interval for checkpoints of all current transcriptions.")

args = ap.parse_args()

CHECKPOINT_INTERVAL = args.chkpt_itv

current_dir = Path(__file__).resolve().parent
path_df = current_dir.parent / f"data/{args.metadat}"#the df containing the video metadata
out_path = current_dir.parent / f"data/{args.out}"#file where output will be saved

df = pd.read_csv(path_df)

df["text"] = ""#add empty column for transcriptions

#if a limit for debugging is enabled: only process the first N rows
if args.limit:
    df = df.head(args.limit)

print(df.head())

#load the whisper model
model = whisper.load_model(args.model)

bad_video_ids = []#list that will contain the ids of all the videos that failed to transcribe

#iterate over the dataframe and add the transcriptions
for i, vid in enumerate(df.itertuples()):
    if vid.media_type != "video":#simply skip the media items that aren't videos
        continue
    mp3_path = str(current_dir.parent / f"data/mp3/{vid.VidID}.mp3")
    try:
        result = model.transcribe(mp3_path)
        df.loc[vid.Index, "text"] = result["text"]#add the transcription to the dataframe
        print(f"{vid.VidID} -> {result["text"]}")
    except Exception as e:
        bad_video_ids.append(str(vid.VidID))#add video id to list
        print(f"Exception: {e}")
        print(f"Transcription problems for video {vid.VidID} -> skipping")
    #save a backup from time to time
    if vid.Index % CHECKPOINT_INTERVAL == 0:
        df.to_csv(str(current_dir.parent / f"data/videos_transcribed_checkpoint_{i}.csv"))

#save final transcriptions
df.to_csv(out_path)

#save list of video ids that couldn't be transcribed:
if len(bad_video_ids):
    transcription_errors_path = str(current_dir.parent / "data/transcription_errors.txt")
    with open(transcription_errors_path, "w", encoding="utf-8") as f:
        f.writelines(bad_video_ids)#write one id per line
    print(f"Saved IDs of all videos with transcription exceptions to:\n {transcription_errors_path}")
else:
    print("All videos transcribed successfully.")