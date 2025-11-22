import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from playwright.sync_api import sync_playwright
from tqdm import tqdm

from spm2ytm.clients.yt_client import search_video_ytdlp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _search_single_song(index: int, song: str) -> tuple[int, str]:
    """
    Worker function to search for a single song.

    Args:
        index: Original position of the song in the list
        song: Song name to search for

    Returns:
        Tuple of (index, video_id) - video_id is empty string if not found
    """
    try:
        video_id = search_video_ytdlp(song)
        if video_id:
            return (index, video_id)
        else:
            logger.warning(f"  ✗ No video found for: {song}")
            return (index, "")
    except Exception as e:
        logger.error(f"  ✗ Error searching for '{song}': {e}")
        return (index, "")


def generate_video_ids_file(song_file_path: str, max_workers: int = 4) -> str:
    """
    Reads a text file with song names (one per line),
    searches YouTube for each song using yt-dlp in parallel,
    and saves the video IDs to a new file with suffix '-ID.txt'.

    Args:
        song_file_path: Path to the text file containing song names
        max_workers: Number of parallel threads for yt-dlp searches (default: 4)

    Returns:
        Path to the generated video IDs file
    """
    logger.info(f"Reading songs from: {song_file_path}")

    song_path = Path(song_file_path)
    if not song_path.exists():
        raise FileNotFoundError(f"Song file not found: {song_file_path}")

    # Read all songs
    with open(song_path, "r", encoding="utf-8") as f:
        songs = [line.strip() for line in f if line.strip()]

    logger.info(f"Found {len(songs)} songs to process")
    logger.info(f"Using {max_workers} parallel workers for yt-dlp searches")

    # Generate output file path
    output_path = song_path.parent / f"{song_path.stem}-ID.txt"

    # Dictionary to store results with preserved order
    results = {}

    # Use ThreadPoolExecutor for parallel searches
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_song = {
            executor.submit(_search_single_song, i, song): (i, song)
            for i, song in enumerate(songs)
        }

        # Process completed tasks with progress bar
        with tqdm(total=len(songs), desc="Searching videos", unit="song") as pbar:
            for future in as_completed(future_to_song):
                index, song = future_to_song[future]
                try:
                    idx, video_id = future.result()
                    results[idx] = video_id
                    if video_id:
                        logger.debug(f"  ✓ [{idx+1}/{len(songs)}] {song} → {video_id}")
                except Exception as e:
                    logger.error(f"  ✗ Unexpected error for '{song}': {e}")
                    results[index] = ""

                pbar.update(1)

    # Reconstruct video_ids list in original order
    video_ids = [results.get(i, "") for i in range(len(songs))]

    # Log summary
    found = sum(1 for vid in video_ids if vid)
    logger.info(f"Search complete: {found}/{len(songs)} videos found")

    # Save video IDs to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(video_ids))

    logger.info(f"Saved {len(video_ids)} video IDs to: {output_path}")

    return str(output_path)


def load_cookies(context, cookies_path: Path):
    """
    Load and sanitize cookies for Playwright from a JSON file.

    Args:
        context: Playwright browser context
        cookies_path: Path to cookies.json file
    """
    if not cookies_path.exists():
        raise FileNotFoundError(f"Missing cookies.json at: {cookies_path}")

    raw = json.loads(cookies_path.read_text())
    fixed = []

    for c in raw:
        # Fix sameSite attribute
        if c.get("sameSite") not in ("Strict", "Lax", "None"):
            c["sameSite"] = "None"

        # Fix expires field
        if "expires" in c:
            if c["expires"] is None:
                del c["expires"]
            elif isinstance(c["expires"], float):
                c["expires"] = int(c["expires"])

        # Fix expiry field
        if "expiry" in c:
            if c["expiry"] is None:
                del c["expiry"]
            elif isinstance(c["expiry"], float):
                c["expiry"] = int(c["expiry"])

        fixed.append(c)

    context.add_cookies(fixed)
    logger.info("Cookies loaded successfully")


def add_videos_to_playlist(
    video_ids_file: str, playlist_name: str, cookies_path: str = "cookies.json"
):
    """
    Uses Playwright to add videos to a YouTube playlist.

    Args:
        video_ids_file: Path to text file containing video IDs (one per line)
        playlist_name: Name of the pre-existing YouTube playlist
        cookies_path: Path to cookies.json file for authentication
    """
    logger.info(f"Starting playlist creation for: {playlist_name}")

    # Read video IDs
    video_ids_path = Path(video_ids_file)
    if not video_ids_path.exists():
        raise FileNotFoundError(f"Video IDs file not found: {video_ids_file}")

    with open(video_ids_path, "r", encoding="utf-8") as f:
        video_ids = [line.strip() for line in f if line.strip()]

    logger.info(f"Found {len(video_ids)} video IDs to add to playlist")

    cookies_file = Path(cookies_path)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Load cookies
        load_cookies(context, cookies_file)

        page = context.new_page()

        # Go to YouTube and verify login
        page.goto("https://www.youtube.com")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if page.locator("button:has-text('Sign in')").is_visible():
            logger.error("Not logged in! Cookies may be invalid.")
            page.screenshot(path="debug_not_logged_in.png")
            context.close()
            browser.close()
            raise Exception("YouTube login failed. Please check cookies.json")

        logger.info("Successfully logged into YouTube")

        # Iterate through video IDs and add to playlist
        successful = 0
        failed = 0

        # Use tqdm for progress bar during playlist addition
        with tqdm(
            total=len(video_ids), desc="Adding to playlist", unit="video"
        ) as pbar:
            for i, video_id in enumerate(video_ids, 1):
                logger.info(f"[{i}/{len(video_ids)}] Processing video ID: {video_id}")

                try:
                    # Navigate to video
                    page.goto(f"https://www.youtube.com/watch?v={video_id}")
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)

                    # Click 3-dot menu
                    three_dot_menu = page.locator(
                        "button.yt-spec-button-shape-next[aria-label='More actions']"
                    ).first
                    three_dot_menu.wait_for(state="visible", timeout=10000)
                    three_dot_menu.click()
                    logger.debug(f"  → Clicked 3-dot menu")
                    time.sleep(1)

                    # Click "Save" option
                    save_option = page.locator(
                        "ytd-menu-service-item-renderer:has-text('Save')"
                    ).first
                    save_option.wait_for(state="visible", timeout=5000)
                    save_option.click()
                    logger.debug(f"  → Clicked Save option")
                    time.sleep(2)

                    # Click on playlist
                    playlist_item = page.locator(
                        f"yt-list-item-view-model[aria-label^='{playlist_name},']"
                    ).first
                    playlist_item.wait_for(state="visible", timeout=5000)
                    playlist_item.click()
                    logger.info(f"  ✓ Added to playlist: {playlist_name}")
                    time.sleep(1)

                    # Close dialog
                    page.keyboard.press("Escape")
                    time.sleep(1)

                    successful += 1

                except Exception as e:
                    logger.error(f"  ✗ Failed to add video {video_id}: {e}")
                    page.screenshot(path=f"debug_error_{video_id}.png")
                    failed += 1
                    # Continue with next video

                pbar.update(1)

        logger.info(f"Finished! Successfully added: {successful}, Failed: {failed}")

        time.sleep(2)
        context.close()
        browser.close()


def create_youtube_playlist_from_spotify(
    song_file_path: str, playlist_name: str, cookies_path: str = "cookies.json"
):
    """
    Complete workflow: Convert Spotify playlist text file to YouTube playlist.

    Args:
        song_file_path: Path to text file with song names (from Spotify)
        playlist_name: Name of pre-existing YouTube playlist
        cookies_path: Path to cookies.json for YouTube authentication
    """
    logger.info("=" * 60)
    logger.info("Starting Spotify → YouTube playlist conversion")
    logger.info("=" * 60)

    # Step 1: Generate video IDs file (with parallel yt-dlp searches)
    logger.info("STEP 1: Generating video IDs from song names...")
    video_ids_file = generate_video_ids_file(song_file_path)

    # Step 2: Add videos to YouTube playlist
    logger.info("STEP 2: Adding videos to YouTube playlist...")
    add_videos_to_playlist(video_ids_file, playlist_name, cookies_path)

    logger.info("=" * 60)
    logger.info("Playlist conversion complete!")
    logger.info("=" * 60)
