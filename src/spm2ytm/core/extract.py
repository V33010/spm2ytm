import logging

from spm2ytm.clients.spotify_client import SpotifyClient
from spm2ytm.utils import clean_string, save_list_to_file

logging.basicConfig(
    level=logging.INFO,  # Set log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[logging.StreamHandler()],  # Print logs to terminal
)
logger = logging.getLogger(__name__)


def extract_liked_songs_to_text(client: SpotifyClient, output_path: str):
    logger.info("Extracting liked songs...")

    tracks = client.get_liked_songs()

    cleaned = [clean_string(f"{t['title']} {t['artist']}") for t in tracks]

    save_list_to_file(cleaned, output_path)
    logger.info(f"Saved liked songs to: {output_path}")

    return cleaned


def extract_playlist_to_text(
    client: SpotifyClient, playlist_url: str, output_path: str
):
    logger.info(f"Extracting playlist → text for {playlist_url}")

    tracks = client.get_playlist_tracks(playlist_url)

    cleaned = [clean_string(f"{t['title']} {t['artist']}") for t in tracks]

    save_list_to_file(cleaned, output_path)
    logger.info(f"Saved playlist songs to: {output_path}")

    return cleaned
