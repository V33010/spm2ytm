import json
import time
from pathlib import Path

import pytest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def get_youtube_client():
    """
    Authenticate using client_secret.json and return a YouTube API client.
    """
    if not Path(CLIENT_SECRET_FILE).exists():
        raise FileNotFoundError("client_secret.json not found in project root.")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    return build("youtube", "v3", credentials=creds)


def find_playlist_by_name(youtube, playlist_name):
    """
    Returns playlist ID if a playlist with the same name already exists.
    Otherwise returns None.
    """
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    response = request.execute()

    for pl in response.get("items", []):
        if pl["snippet"]["title"] == playlist_name:
            return pl["id"]

    return None


def create_playlist(youtube, playlist_name, description="Created via pytest"):
    """
    Creates a playlist and returns its ID.
    """
    body = {
        "snippet": {"title": playlist_name, "description": description},
        "status": {"privacyStatus": "private"},
    }

    request = youtube.playlists().insert(part="snippet,status", body=body)
    response = request.execute()
    return response["id"]


def add_video_to_playlist(youtube, playlist_id, video_id):
    """
    Adds a single video to the playlist.
    """
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
    }

    request = youtube.playlistItems().insert(part="snippet", body=body)
    return request.execute()


@pytest.mark.parametrize("playlist_name", ["sample_playlist_1"])
def test_create_or_find_and_add_items(playlist_name):
    youtube = get_youtube_client()

    # 1️⃣ Check if playlist exists
    existing_id = find_playlist_by_name(youtube, playlist_name)

    if existing_id:
        print(f"Playlist '{playlist_name}' already exists → Using ID: {existing_id}")
        playlist_id = existing_id
    else:
        print(f"Playlist '{playlist_name}' not found → Creating new playlist…")
        playlist_id = create_playlist(youtube, playlist_name)

        # Delay for safety because YouTube indexing is slow
        time.sleep(2)

    assert playlist_id is not None

    # 2️⃣ Add two test videos
    test_video_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0"]  # rickroll  # gangnam style

    for vid in test_video_ids:
        try:
            add_video_to_playlist(youtube, playlist_id, vid)
        except HttpError as e:
            pytest.fail(f"Failed to add video {vid}: {e}")

    print("All test operations completed successfully.")
