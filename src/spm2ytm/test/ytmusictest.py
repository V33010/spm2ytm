import os

from dotenv import load_dotenv
from ytmusicapi import OAuthCredentials, YTMusic

load_dotenv()


YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")

ytmusic = YTMusic(
    "oauth.json",
    oauth_credentials=OAuthCredentials(
        client_id=YT_CLIENT_ID, client_secret=YT_CLIENT_SECRET
    ),
)
playlistId = ytmusic.create_playlist("test", "test description")
search_results = ytmusic.search("Oasis Wonderwall")
ytmusic.add_playlist_items(playlistId, [search_results[0]["videoId"]])
