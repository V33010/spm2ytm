import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class YouTubeClient:
    """
    Wrapper for YouTube Data API v3
    Handles:
    - Creating playlists
    - Searching songs
    - Adding videos to playlists
    """

    def __init__(self):
        creds_path = os.path.join(os.getcwd(), "oauth.json")

        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"oauth.json not found in current working directory: {creds_path}"
            )

        self.creds = Credentials.from_authorized_user_file(
            creds_path,
            scopes=[
                "https://www.googleapis.com/auth/youtube",
                "https://www.googleapis.com/auth/youtube.force-ssl",
            ],
        )

        self.youtube = build("youtube", "v3", credentials=self.creds)

    def create_playlist(self, title: str, description: str = "") -> str:
        request = self.youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "private"},
            },
        )
        response = request.execute()
        return response["id"]

    def search_song(self, query: str) -> str | None:
        request = self.youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1,
            videoCategoryId="10",  # Music category
        )
        response = request.execute()

        items = response.get("items", [])
        if not items:
            return None

        return items[0]["id"]["videoId"]

    def add_song_to_playlist(self, playlist_id: str, video_id: str):
        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        )
        request.execute()
