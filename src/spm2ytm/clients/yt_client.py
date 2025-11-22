import re

from yt_dlp import YoutubeDL


def search_video_ytdlp(query: str) -> str | None:
    """
    Searches YouTube using yt-dlp and returns the first video's ID.

    Rules:
    - Query may contain: letters, numbers, spaces, underscores.
    - Uses yt-dlp's 'ytsearch1:' to fetch only the top result.

    Returns:
        video_id (str) if found, otherwise None.
    """

    # ------------------------
    # Validate query
    # ------------------------
    if not re.fullmatch(r"[A-Za-z0-9_ ]+", query):
        raise ValueError(
            "Query may only contain letters, numbers, spaces, and underscores."
        )

    # ------------------------
    # yt-dlp search
    # ------------------------
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,  # faster, metadata only
    }

    search_term = f"ytsearch1:{query}"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_term, download=False)

    # ------------------------
    # Process response
    # ------------------------
    entries = info.get("entries", [])
    if not entries:
        return None

    first = entries[0]

    # id is guaranteed in extract_flat mode
    video_id = first.get("id")
    return video_id


if __name__ == "__main__":

    video_id = search_video_ytdlp("Drake Views")

    print(video_id)
