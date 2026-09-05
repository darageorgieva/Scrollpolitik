import whisper
from pathlib import Path
import pandas as pd

CHECKPOINT_INTERVAL = 2

current_dir = Path(__file__).resolve().parent
path_df = current_dir.parent / "data/video_metadata_media_type.csv"#the df containing the metadata and party affiliation
path_df_checkpoint = current_dir.parent / "data/videos_transcribed.csv"

df = pd.read_csv(path_df)

df["text"] = ""#add empty column for transcriptions

#for debugging: only do the first 10 videos
df = df.head(10)

print(df.head())

#load the whisper model
model = whisper.load_model("turbo")

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
    except:
        bad_video_ids.append(str(vid.VidID))#add video id to list
        print(f"Transcription problems for video {vid.VidID} -> skipping")

    #save a backup from time to time
    if vid.Index % CHECKPOINT_INTERVAL == 0:
        df.to_csv(str(current_dir.parent / f"data/videos_transcribed_checkpoint_{vid.Index}.csv"))

#save final transcriptions
df.to_csv(str(current_dir.parent / f"data/videos_transcribed.csv"))

#save list of video ids that couldn't be transcribed:
if len(bad_video_ids):
    transcription_errors_path = str(current_dir.parent / "data/transcription_errors.txt")
    with open(transcription_errors_path, "w", encoding="utf-8") as f:
        f.writelines(bad_video_ids)#write one id per line
    print(f"Saved IDs of all videos with transcription exceptions to:\n {transcription_errors_path}")
else:
    print("All videos transcribed successfully.")