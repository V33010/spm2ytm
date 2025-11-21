import os
from typing import List

from spm2ytm.clients.yt_client import YouTubeClient


def load_songs_from_text(file_path: str) -> List[str]:
    """
    Reads a text file and returns a list of songs (one per line).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Text file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        songs = [line.strip() for line in f.readlines() if line.strip()]

    return songs


def create_yt_playlist_from_text(file_path: str, playlist_name: str) -> str:
    """
    Creates a YouTube playlist using the normal YouTube Data API (NOT YouTube Music API)
    and fills it with songs from a .txt file.
    """

    print(f"📄 Loading songs from: {file_path}")
    songs = load_songs_from_text(file_path)

    yt = YouTubeClient()

    print(f"🎵 Creating YouTube playlist: {playlist_name}")
    playlist_id = yt.create_playlist(
        playlist_name, description="Imported using spm2ytm"
    )

    print(f"🔍 Searching & adding songs...")
    for song in songs:
        print(f" → Searching: {song}")
        video_id = yt.search_song(song)

        if not video_id:
            print(f"   ❌ No result found for: {song}")
            continue

        yt.add_song_to_playlist(playlist_id, video_id)
        print(f"   ✅ Added: {song}")

    print(f"\n🎉 Playlist created successfully!")
    print(f"Playlist URL: https://www.youtube.com/playlist?list={playlist_id}")

    return playlist_id
