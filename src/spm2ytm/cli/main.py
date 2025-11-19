import os
import re

import click
from dotenv import load_dotenv

from spm2ytm.clients.spotify_client import SpotifyClient
from spm2ytm.core.extract import (extract_liked_songs_to_text,
                                  extract_playlist_to_text)

# Load .env into the shell environment
load_dotenv()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("playlist_url")
@click.argument("output_path", required=False)
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
def playlist(playlist_url, output_path, client_id, client_secret, redirect_uri):
    """Extract any playlist to text."""

    # Default output folder
    if not output_path:
        output_path = os.path.join("..", "data", "playlists")
    os.makedirs(output_path, exist_ok=True)

    client = SpotifyClient(client_id, client_secret, redirect_uri)

    # Get playlist ID and name
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    playlist_info = client.sp.playlist(playlist_id)
    playlist_name = playlist_info.get("name", "")

    # Sanitize playlist name: only alphanumerics and spaces
    sanitized_name = re.sub(r"[^A-Za-z0-9 ]+", "", playlist_name).strip()
    # Replace all spaces with underscores
    sanitized_name = sanitized_name.replace(" ", "_")

    # Build filename
    if sanitized_name:
        filename = f"{playlist_id}-{sanitized_name}.txt"
    else:
        filename = f"{playlist_id}.txt"

    file_path = os.path.join(output_path, filename)

    # Extract playlist to text
    extract_playlist_to_text(client, playlist_url, file_path)
    click.echo(f"Playlist saved to {file_path}")


@cli.command()
@click.argument("output_path", required=False)
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
def liked(output_path, client_id, client_secret, redirect_uri):
    """Extract liked songs to text."""

    # Default output folder
    if not output_path:
        output_path = os.path.join("..", "data", "liked_songs")
    os.makedirs(output_path, exist_ok=True)

    # Build filename for liked songs
    file_path = os.path.join(output_path, "liked_songs.txt")

    client = SpotifyClient(client_id, client_secret, redirect_uri)
    extract_liked_songs_to_text(client, file_path)
    click.echo(f"Liked songs saved to {file_path}")


if __name__ == "__main__":
    cli()
