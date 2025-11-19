from pathlib import Path

from ..clients.yt_music_client import YTMusicClient


def create_yt_playlist_from_text(
    text_file: str, playlist_name: str, yt_auth_file: str = "headers_auth.json"
):
    """
    Reads a text file of songs, searches YouTube Music, and creates a playlist.

    :param text_file: Path to the text file with 1 song per line
    :param playlist_name: Name of the YouTube Music playlist to create
    :param yt_auth_file: Path to YTMusic auth headers
    """
    text_path = Path(text_file)
    if not text_path.exists():
        raise FileNotFoundError(f"{text_file} does not exist.")

    yt_client = YTMusicClient(auth_file=yt_auth_file)
    playlist_id = yt_client.create_playlist(playlist_name)
    print(f"Created playlist '{playlist_name}' with ID {playlist_id}")

    video_ids = []
    with text_path.open("r", encoding="utf-8") as f:
        for line in f:
            query = line.strip()
            if not query:
                continue
            video_id = yt_client.search_song(query)
            if video_id:
                video_ids.append(video_id)
                print(f"Found '{query}' → {video_id}")
            else:
                print(f"Song not found: {query}")

    # Add all songs in one batch
    yt_client.add_songs_to_playlist(playlist_id, video_ids)
    print(f"Added {len(video_ids)} songs to '{playlist_name}'")
