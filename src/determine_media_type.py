import requests
import pandas as pd
from pathlib import Path
import time

current_dir = Path(__file__).resolve().parent
metadata_file_path = current_dir.parent / "data/video_metadata.csv"
out_path = current_dir.parent / "data/video_metadata_media_type.csv"#path where to save the dataframe that also contains the media type for each post

output_df = pd.read_csv(metadata_file_path)

print("Infer for every post whether it is a video or photo:")

#NEXT:  query each item to determine whether it is a photo or a video:
#add an empty column for media type
output_df["media_type"] = ""
headers={
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        )
    }
for n_processed, row in enumerate(output_df.itertuples(), start=1):
    if n_processed % 20 == 0:
        output_df.to_csv(out_path, index=False)#make a backup every once in a while
        print(f"Saved latest backup to: {out_path}")
        print(f"Continuing to infer media types. Currently at: {n_processed} items.")
    url = f"https://www.tiktok.com/@{row.UserID}/video/{row.VidID}"
    try:
        response = requests.get(url, headers, timeout=10)
        response.raise_for_status()
        html = response.text
        if "webapp.browserRedirect-context" in html:
            output_df.loc[row.Index, "media_type"] = "photo"
            print(f"Found photo for: {url}")
        else:
            output_df.loc[row.Index, "media_type"] = "video"
    except:
        print(f"Problems querying media type for media {url}\nMarking with type \"unknown\".")
        output_df.loc[row.Index, "media_type"] = "unknown"
    time.sleep(1)

print(f"Finished infering media type for {n_processed} items.")
output_df.to_csv(out_path_media_type, index=False)
print(f"Saved to: {str(out_path_media_type)}")