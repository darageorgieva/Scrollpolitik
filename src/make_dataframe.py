from pathlib import Path
import pandas as pd

current_dir = Path(__file__).resolve().parent
audio_file_path = current_dir.parent / "data/mp3/kicklherbert_7409992801452182817.mp3"
metadata_file_path = current_dir.parent / "data/video_metadata.jsonl"

#metadata_df = pd.DataFrame(columns=["id", "username", "view_count", "like_count", "share_count", "comment_count", "create_time", "video_duration"])

metadata_df = pd.read_json(metadata_file_path, lines=True)
metadata_df = metadata_df.drop(columns=["queried_username"])
renaming = {
    "id": "VidID",
    "username": "UserID",
    "view_count": "ViewCount",
    "like_count": "LikeCount",
    "share_count": "ShareCount",
    "comment_count": "CommentCount",
    "create_time": "create_time",#create time is not the same as "Date" from the Sololev DF, so let's don't adopt their name
    "video_duration": "video_duration"
    }
metadata_df.rename(columns=renaming, inplace=True)

print(metadata_df.head())

#CONTINUE: merge with account_person_mapping to get the party affiliations into the df