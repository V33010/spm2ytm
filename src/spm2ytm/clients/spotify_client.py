import logging
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

logging.basicConfig(
    level=logging.INFO,  # Set log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[logging.StreamHandler()],  # Print logs to terminal
)
logger = logging.getLogger(__name__)


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        logger.info("Initializing Spotify client...")

        # Use a cache file in the user's home directory
        cache_path = os.path.join(os.path.expanduser("~"), ".cache_spotify")

        self.oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-library-read playlist-read-private",
            cache_path=cache_path,
            show_dialog=True,
            open_browser=False,  # disable auto browser
        )

        # Get token (either cached or manual)
        token = self._get_token()
        self.sp = spotipy.Spotify(auth=token)

        logger.info("Spotify client initialized.")

    def _get_token(self) -> str:
        """Retrieve Spotify token, prompt manually if necessary."""
        token_info = self.oauth.get_cached_token()

        # If cached token exists and is valid, use it
        if token_info and not self.oauth.is_token_expired(token_info):
            return token_info["access_token"]

        # Otherwise, need user to authorize manually
        auth_url = self.oauth.get_authorize_url()
        print("\nPlease open this URL in your browser and authorize:")
        print(auth_url)
        print(
            "\nAfter redirect, copy the full URL you were redirected to and paste here."
        )
        response = input("Enter the full redirect URL: ").strip()

        # Extract code and fetch access token
        code = self.oauth.parse_response_code(response)
        token_info = self.oauth.get_access_token(code, as_dict=True)

        return token_info["access_token"]

    def get_liked_songs(self) -> list[dict]:
        """Fetch all liked songs."""
        logger.info("Fetching liked songs...")

        tracks = []
        results = self.sp.current_user_saved_tracks()

        while results:
            for item in results["items"]:
                track = item["track"]
                tracks.append(
                    {
                        "title": track["name"],
                        "artist": (
                            track["artists"][0]["name"] if track["artists"] else ""
                        ),
                    }
                )

            results = self.sp.next(results) if results.get("next") else None

        logger.info(f"Fetched {len(tracks)} liked songs.")
        return tracks

    def get_playlist_tracks(self, playlist_url: str) -> list[dict]:
        """Fetch tracks from a given playlist link."""
        logger.info(f"Fetching Spotify playlist: {playlist_url}")

        playlist_id = playlist_url.split("/")[-1].split("?")[0]
        results = self.sp.playlist_items(playlist_id)
        tracks = []

        while results:
            for item in results["items"]:
                track = item["track"]
                if track:
                    tracks.append(
                        {
                            "title": track["name"],
                            "artist": (
                                track["artists"][0]["name"] if track["artists"] else ""
                            ),
                        }
                    )

            results = self.sp.next(results) if results.get("next") else None

        logger.info(f"Fetched {len(tracks)} tracks from playlist.")
        return tracks
