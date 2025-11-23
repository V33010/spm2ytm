import os
import re

import click
from dotenv import load_dotenv

from spm2ytm.clients.spotify_client import SpotifyClient
from spm2ytm.core.create import create_youtube_playlist_from_spotify
from spm2ytm.core.extract import (extract_liked_songs_to_text,
                                  extract_playlist_to_text)

# Load .env into the shell environment
load_dotenv()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("playlist_url")
@click.argument("action", required=False)
@click.argument("youtube_playlist_name", required=False)
@click.option(
    "--output-path", required=False, help="Custom output directory for playlist file"
)
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
@click.option(
    "--cookies-path", default="cookies.json", help="Path to YouTube cookies.json file"
)
def playlist(
    playlist_url,
    action,
    youtube_playlist_name,
    output_path,
    client_id,
    client_secret,
    redirect_uri,
    cookies_path,
):
    """Extract Spotify playlist to text file, optionally create YouTube playlist.

    Usage:
        playlist <spotify_url>                          - Extract only
        playlist <spotify_url> ytp <youtube_playlist>   - Extract + Create YouTube playlist
    """

    # Default output folder
    if not output_path:
        output_path = os.path.join("data", "playlists")
    os.makedirs(output_path, exist_ok=True)

    client = SpotifyClient(client_id, client_secret, redirect_uri)

    # Get playlist ID and name
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    playlist_info = client.sp.playlist(playlist_id)
    playlist_name = playlist_info.get("name", "")

    # Sanitize playlist name: only alphanumerics and spaces
    sanitized_name = re.sub(r"[^A-Za-z0-9 ]+", "", playlist_name).strip()
    sanitized_name = sanitized_name.replace(" ", "_")

    # Build filename
    if sanitized_name:
        filename = f"{playlist_id}-{sanitized_name}.txt"
    else:
        filename = f"{playlist_id}.txt"

    file_path = os.path.join(output_path, filename)

    # Extract playlist to text
    extract_playlist_to_text(client, playlist_url, file_path)
    click.echo(f"✓ Playlist saved to {file_path}")

    # Check if user wants to create YouTube playlist
    if action == "ytp":
        if not youtube_playlist_name:
            click.echo("Error: YouTube playlist name required after 'ytp'", err=True)
            return

        click.echo(f"\n▶ Starting YouTube playlist creation...")
        click.echo(f"  Target YouTube playlist: {youtube_playlist_name}")

        try:
            create_youtube_playlist_from_spotify(
                song_file_path=file_path,
                playlist_name=youtube_playlist_name,
                cookies_path=cookies_path,
            )
            click.echo(f"\n✓ Successfully created YouTube playlist!")
        except Exception as e:
            click.echo(f"\n✗ Error creating YouTube playlist: {e}", err=True)

    elif action is not None:
        click.echo(
            f"Warning: Unknown action '{action}'. Use 'ytp' to create YouTube playlist.",
            err=True,
        )


@cli.command()
@click.argument("youtube_playlist_name")
@click.option(
    "--song-file",
    required=True,
    type=click.Path(exists=True),
    help="Path to text file containing song names (one per line)",
)
@click.option(
    "--cookies-path", default="cookies.json", help="Path to YouTube cookies.json file"
)
def ytp(youtube_playlist_name, song_file, cookies_path):
    """Create YouTube playlist from a custom song file (bypasses Spotify extraction).

    Usage:
        ytp <youtube_playlist_name> --song-file <path> --cookies-path <path>
    """
    click.echo(f"▶ Creating YouTube playlist from custom song file")
    click.echo(f"  Song file: {song_file}")
    click.echo(f"  Target YouTube playlist: {youtube_playlist_name}")
    click.echo(f"  Cookies: {cookies_path}")

    # Verify song file exists
    if not os.path.exists(song_file):
        click.echo(f"✗ Error: Song file not found at {song_file}", err=True)
        return

    try:
        create_youtube_playlist_from_spotify(
            song_file_path=song_file,
            playlist_name=youtube_playlist_name,
            cookies_path=cookies_path,
        )
        click.echo(f"\n✓ Successfully created YouTube playlist!")
    except Exception as e:
        click.echo(f"\n✗ Error creating YouTube playlist: {e}", err=True)


@cli.command()
@click.argument("output_path", required=False)
@click.option("--client-id", envvar="SPOTIFY_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="SPOTIFY_CLIENT_SECRET", required=True)
@click.option("--redirect-uri", envvar="SPOTIFY_REDIRECT_URI", required=True)
def liked(output_path, client_id, client_secret, redirect_uri):
    """Extract liked songs to text."""

    # Default output folder
    if not output_path:
        output_path = os.path.join("data", "liked_songs")
    os.makedirs(output_path, exist_ok=True)

    # Build filename for liked songs
    file_path = os.path.join(output_path, "liked_songs.txt")

    client = SpotifyClient(client_id, client_secret, redirect_uri)
    extract_liked_songs_to_text(client, file_path)
    click.echo(f"Liked songs saved to {file_path}")


if __name__ == "__main__":
    cli()
