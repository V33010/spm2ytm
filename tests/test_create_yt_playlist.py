import os

import pytest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# YouTube scope to modify playlists
SCOPES = ["https://www.googleapis.com/auth/youtube"]


@pytest.mark.integration
def test_create_youtube_playlist_standalone():
    """
    Standalone test:
    - Authenticates using client_secret.json
    - Creates a playlist named 'sample_playlist_1'
    - Verifies that a playlist ID is returned
    """

    client_secret_path = os.path.abspath("client_secret.json")
    assert os.path.exists(client_secret_path), "client_secret.json not found!"

    # Step 1 — OAuth Flow
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Step 2 — Build API client
    youtube = build("youtube", "v3", credentials=creds)

    # Step 3 — Create playlist
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "sample_playlist_1",
                "description": "Test playlist from standalone pytest",
            },
            "status": {"privacyStatus": "private"},
        },
    )

    response = request.execute()

    # Step 4 — Assert playlist creation
    playlist_id = response.get("id")
    print("Created playlist:", playlist_id)

    assert playlist_id is not None, "Playlist creation failed!"
