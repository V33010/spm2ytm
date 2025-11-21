import time

from googleapiclient.errors import HttpError

# -------------------------
# YouTube Playlist Helpers
# -------------------------


def create_playlist(yt, title, description=""):
    """
    Creates a private YouTube playlist and returns its ID.
    """
    try:
        req = yt.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "private"},
            },
        )
        res = req.execute()
        print(f"Created YouTube playlist '{title}' (ID: {res['id']})")
        return res["id"]
    except HttpError as e:
        print(f"Error creating playlist '{title}': {e}")
        return None


def search_video(yt, query, retries=3, delay=2):
    """
    Searches YouTube and returns the first video's ID.
    """
    for attempt in range(1, retries + 1):
        try:
            req = yt.search().list(
                part="id,snippet",
                q=query,
                maxResults=1,
                type="video",
            )
            res = req.execute()
            items = res.get("items", [])
            if not items:
                return None
            return items[0]["id"]["videoId"]
        except HttpError as e:
            if e.resp.status in [500, 503, 409] and attempt < retries:
                print(
                    f"Warning: Temporary error searching '{query}' (attempt {attempt}). Retrying..."
                )
                time.sleep(delay)
                delay *= 2
                continue
            elif e.resp.status == 403 and "quotaExceeded" in str(e):
                print(
                    "Quota exceeded while searching videos. Stopping further searches."
                )
                return None
            else:
                print(f"Error searching video '{query}': {e}")
                return None
    return None


def add_video_to_playlist(yt, playlist_id, video_id, retries=3, delay=2):
    """
    Inserts a video into a playlist, with retry for transient errors.
    """
    for attempt in range(1, retries + 1):
        try:
            req = yt.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            return req.execute()
        except HttpError as e:
            if e.resp.status in [500, 503, 409] and attempt < retries:
                print(
                    f"Warning: Temporary error adding video (attempt {attempt}). Retrying..."
                )
                time.sleep(delay)
                delay *= 2
                continue
            elif e.resp.status == 403 and "quotaExceeded" in str(e):
                print("Quota exceeded while adding videos. Stopping further additions.")
                return None
            else:
                print(f"Error adding video {video_id}: {e}")
                return None
    return None


def create_playlist_and_add_tracks(yt, playlist_name, track_queries, delay_between=0.5):
    """
    High-level helper:
    - Creates playlist
    - Searches & adds tracks
    - Returns playlist ID

    Shows progress while adding tracks and stops gracefully if quota exceeded.
    """
    playlist_id = create_playlist(yt, playlist_name)
    if not playlist_id:
        print("Playlist creation failed. Aborting.")
        return None

    total = len(track_queries)
    added = 0

    print(f"Adding {total} tracks to playlist '{playlist_name}'...")

    for idx, track in enumerate(track_queries, start=1):
        video_id = search_video(yt, track)
        if video_id is None:
            print(f"[{idx}/{total}] Track not found or quota exceeded: {track}")
            if "quotaExceeded" in str(video_id):
                break
            continue

        result = add_video_to_playlist(yt, playlist_id, video_id)
        if result:
            added += 1
            print(f"[{idx}/{total}] Added: {track}")
        else:
            print(f"[{idx}/{total}] Failed to add: {track}")
            # Stop if quota exceeded during addition
            if result is None and "Quota exceeded" in str(result):
                break

        time.sleep(delay_between)  # avoid hitting rate limits

    print(f"Done! {added}/{total} tracks added to YouTube playlist '{playlist_name}'.")
    return playlist_id
