import os
import re

import click
from dotenv import load_dotenv

from spm2ytm.clients.spotify_client import SpotifyClient
from spm2ytm.clients.yt_client import get_youtube_client
from spm2ytm.core.create import create_playlist_and_add_tracks
from spm2ytm.core.extract import (extract_liked_songs_to_text,
                                  extract_playlist_to_text)

# Load .env into the shell environment
load_dotenv()


@click.group()
def cli():
    pass


# -------------------------
# PLAYLIST COMMAND
# -------------------------
@cli.command()
@click.argument("playlist_url")
@click.option(
    "--yt",
    "youtube_playlist_name",
    required=False,
    help="YouTube playlist name to create and add tracks",
)
@click.argument("output_path", required=False)
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
def playlist(
    playlist_url,
    youtube_playlist_name,
    output_path,
    client_id,
    client_secret,
    redirect_uri,
):
    """Extract a Spotify playlist to a text file, optionally create a YouTube playlist and add songs."""

    # Default output folder
    if not output_path:
        output_path = os.path.join("..", "data", "playlists")

    os.makedirs(output_path, exist_ok=True)

    client = SpotifyClient(client_id, client_secret, redirect_uri)

    # Extract playlist ID
    playlist_id = playlist_url.split("/")[-1].split("?")[0]

    # Query playlist info from Spotify
    playlist_info = client.sp.playlist(playlist_id)
    playlist_name = playlist_info.get("name", "")

    # Sanitize playlist name (alphanumeric + underscores)
    sanitized_name = re.sub(r"[^A-Za-z0-9 ]+", "", playlist_name).strip()
    sanitized_name = sanitized_name.replace(" ", "_")

    # Generate file name
    if sanitized_name:
        filename = f"{playlist_id}-{sanitized_name}.txt"
    else:
        filename = f"{playlist_id}.txt"

    file_path = os.path.join(output_path, filename)

    # Extract playlist tracks to text file
    extract_playlist_to_text(client, playlist_url, file_path)
    click.echo(f"Playlist saved to {file_path}")

    # -------------------------
    # Optional: YouTube integration
    # -------------------------
    if youtube_playlist_name:
        click.echo("Starting YouTube playlist creation...")

        yt_client = get_youtube_client()

        # Read the extracted Spotify text file
        with open(file_path, "r", encoding="utf-8") as f:
            tracks = [line.strip() for line in f if line.strip()]

        if not tracks:
            click.echo(
                "No tracks found in the text file. Aborting YouTube playlist creation."
            )
            return

        # Create YouTube playlist and add tracks
        yt_playlist_id = create_playlist_and_add_tracks(
            yt_client, youtube_playlist_name, tracks
        )
        click.echo(
            f"YouTube playlist '{youtube_playlist_name}' created successfully! Playlist ID: {yt_playlist_id}"
        )


# -------------------------
# LIKED SONGS COMMAND
# -------------------------
@cli.command()
@click.argument("output_path", required=False)
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
def liked(output_path, client_id, client_secret, redirect_uri):
    """Extract liked songs to a text file."""

    # Default output folder
    if not output_path:
        output_path = os.path.join("..", "data", "liked_songs")

    os.makedirs(output_path, exist_ok=True)

    # Filename for liked songs
    file_path = os.path.join(output_path, "liked_songs.txt")

    client = SpotifyClient(client_id, client_secret, redirect_uri)

    extract_liked_songs_to_text(client, file_path)

    click.echo(f"Liked songs saved to {file_path}")


if __name__ == "__main__":
    cli()
