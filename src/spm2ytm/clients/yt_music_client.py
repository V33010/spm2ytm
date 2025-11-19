from ytmusicapi import YTMusic


class YTMusicClient:
    def __init__(self, auth_file: str = "headers_auth.json"):
        """
        Initialize YTMusic client using headers_auth.json obtained from YouTube Music.
        """
        self.client = YTMusic(auth_file)

    def create_playlist(self, playlist_name: str, description: str = "") -> str:
        """
        Create a new playlist and return the playlist ID.
        """
        playlist_id = self.client.create_playlist(
            title=playlist_name, description=description
        )
        return playlist_id

    def search_song(self, query: str) -> str:
        """
        Search for a song and return the first videoId found.
        """
        results = self.client.search(query, filter="songs")
        if not results:
            return None
        return results[0]["videoId"]

    def add_songs_to_playlist(self, playlist_id: str, video_ids: list[str]):
        """
        Add list of videoIds to a YouTube Music playlist.
        """
        if video_ids:
            self.client.add_playlist_items(playlist_id, video_ids)
