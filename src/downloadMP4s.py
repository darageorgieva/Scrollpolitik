import random
import time
from pathlib import Path
import pandas as pd

import yt_dlp

def download_tiktoks(filepath, output_dir):
    """
    Download TikTok videos listed in a JSONL file.

    Each line of the input file should contain an object with at least:
        {
            "id": 7420191742353296673,
            "username": "kicklherbert"
        }

    Videos are downloaded as MP4 files into `output_dir`.

    Downloads are performed sequentially with randomized delays to
    reduce the likelihood of triggering TikTok rate limits.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    # yt-dlp options
    ydl_opts = {
        # Prefer MP4-compatible video/audio and merge them into MP4.
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",

        # Output filename: username + TikTok ID
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),

        # Don't download videos that already exist.
        "nooverwrites": True,

        # Add delays between HTTP requests made by yt-dlp.
        "sleep_interval_requests": 2,
        "max_sleep_interval_requests": 5,

        # Be conservative with retries.
        "retries": 3,
        "fragment_retries": 3,

        # Don't flood the server with concurrent fragments.
        "concurrent_fragment_downloads": 1,

        # Less noisy output.
        "quiet": False,
    }


    #now make a list of all the videos (so filtering out all the photos or unknowns)
    df_metadata = pd.read_csv(filepath)
    videos = []#will contain all videos
    for row in df_metadata.itertuples():
        if row.media_type == "video":
            videos.append((row.UserID, row.VidID))#append a tuple containing the username and video id for a media item

    print(f"Found {len(videos)} videos to download.")

    # Create the yt-dlp downloader once and reuse it.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        for index, video in enumerate(videos, start=1):
            username = video[0]
            video_id = video[1]

            url = f"https://www.tiktok.com/@{username}/video/{video_id}"

            print(
                f"\n[{index}/{len(videos)}] "
                f"Downloading @{username} / {video_id}"
            )
            print(f"URL: {url}")

            try:
                ydl.download([url])
                print("Download successful.")

            except Exception as e:
                print(f"Download failed: {e}")

            # Wait before starting the next TikTok.
            # Randomizing the delay makes the request pattern less regular.
            if index < len(videos):
                delay = random.uniform(15, 30)
                print(f"Waiting {delay:.1f} seconds before next download...")
                time.sleep(delay)

    print("\nFinished.")

#little test:

current_dir = Path(__file__).resolve().parent
video_metadata_path = current_dir.parent / "data/video_metadata_media_type.csv"
output_dir = current_dir.parent / "data/mp4"

download_tiktoks(filepath=video_metadata_path, output_dir=output_dir)