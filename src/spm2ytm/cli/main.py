import os
import re

import click
from dotenv import load_dotenv

from spm2ytm.clients.spotify_client import SpotifyClient
from spm2ytm.core.create import create_yt_playlist_from_text
from spm2ytm.core.extract import (extract_liked_songs_to_text,
                                  extract_playlist_to_text)

# Load .env into the shell environment
load_dotenv()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("playlist_url")
@click.argument("ytm", required=False)
@click.argument("yt_playlist_name", required=False)
@click.option("--output-path", default=None, help="Folder to save Spotify text file")
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
@click.option(
    "--yt-auth-file",
    envvar="YTM_AUTH_FILE",
    default=None,
    help="Path to YTMusic auth headers JSON",
)
def playlist(
    playlist_url,
    ytm,
    yt_playlist_name,
    output_path,
    client_id,
    client_secret,
    redirect_uri,
    yt_auth_file,
):
    """
    Extract Spotify playlist to text file.

    To create YouTube Music playlist as well, use:
    playlist <spotify_playlist_link> ytm <youtube_music_playlist_name>
    """
    # Default output folder
    if not output_path:
        output_path = os.path.join("..", "data", "playlists")
    os.makedirs(output_path, exist_ok=True)

    client = SpotifyClient(client_id, client_secret, redirect_uri)

    # Get playlist ID and name
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    playlist_info = client.sp.playlist(playlist_id)
    playlist_name = playlist_info.get("name", "")

    # Sanitize playlist name for text file
    sanitized_name = re.sub(r"[^A-Za-z0-9 ]+", "", playlist_name).strip()
    sanitized_name = sanitized_name.replace(" ", "_")

    # Build filename for text file
    if sanitized_name:
        filename = f"{playlist_id}-{sanitized_name}.txt"
    else:
        filename = f"{playlist_id}.txt"

    file_path = os.path.join(output_path, filename)

    # Extract playlist to text file
    extract_playlist_to_text(client, playlist_url, file_path)
    click.echo(f"Spotify playlist saved to: {file_path}")

    # If 'ytm' argument is supplied, do YouTube Music creation
    if ytm:
        if ytm.lower() != "ytm":
            click.echo(
                "Error: second argument must be 'ytm' to trigger YouTube Music creation."
            )
            return
        if not yt_playlist_name:
            click.echo(
                "Error: You must provide a YouTube Music playlist name after 'ytm'."
            )
            return
        # Validate playlist name: only alphanumeric, no spaces
        if not re.fullmatch(r"[A-Za-z0-9]+", yt_playlist_name):
            click.echo(
                "Error: YouTube Music playlist name must be alphanumeric with no whitespace."
            )
            return

        # Create YouTube Music playlist using the text file
        click.echo(f"Creating YouTube Music playlist '{yt_playlist_name}'...")
        create_yt_playlist_from_text(
            text_file=file_path,
            playlist_name=yt_playlist_name,
            yt_auth_file=yt_auth_file,
        )
        click.echo(
            f"Playlist '{yt_playlist_name}' created successfully on YouTube Music."
        )


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
    click.echo(f"Liked songs saved to: {file_path}")


if __name__ == "__main__":
    cli()
