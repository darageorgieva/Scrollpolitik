from pathlib import Path
import pandas as pd
import requests
import time

current_dir = Path(__file__).resolve().parent
metadata_file_path = current_dir.parent / "data/video_metadata.jsonl"
account_person_mapping_path = current_dir.parent / "data/Deutsche Politik auf Tik Tok - Eine Sammlung von Martin Fuchs @wahl_beobachter.xlsx"
out_path = current_dir.parent / "data/video_metadata.csv"

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
account_person_mapping_df = pd.read_excel(account_person_mapping_path, skiprows=1)

account_person_mapping_df = account_person_mapping_df[~account_person_mapping_df["Tik Tok-Profil"].isna()]#only keep the rows where we have profiles

def extract_name(profile_url:str) -> str:
    name = profile_url.split("@")[-1].rstrip()
    return name

account_person_mapping_df["profile_name"] = account_person_mapping_df["Tik Tok-Profil"].apply(extract_name)

account_person_mapping_df = account_person_mapping_df[["Partei", "profile_name"]]

output_df = pd.merge(metadata_df, account_person_mapping_df, left_on="UserID", right_on="profile_name", how="left")
output_df = output_df.drop(columns=["profile_name"])#don't need to keep duplicate column
output_df.rename(columns={"Partei":"party"}, inplace=True)

print(output_df.head())

output_df.to_csv(out_path, index=False)
print(f"Wrote the dataframe to {str(out_path)}")

##  the following is only debug code used to work with the austria data (cuz that's what I have right now for testing)

# account_person_mapping_df = pd.read_csv((current_dir.parent / "data/account_person_mapping_debug.csv"))

# account_person_mapping_df = account_person_mapping_df[["party", "tiktok_username"]]

# output_df = pd.merge(metadata_df, account_person_mapping_df, left_on="UserID", right_on="tiktok_username", how="left")
# output_df = output_df.drop(columns=["tiktok_username"])#don't need to keep duplicate column

# print(output_df.head())

# output_df.to_csv(out_path, index=False)