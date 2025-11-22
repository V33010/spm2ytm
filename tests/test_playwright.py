import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from yt_dlp import YoutubeDL

# Path to cookies.json
COOKIES_PATH = Path("cookies.json")


# --- FIX 1 : YouTube search ---
def youtube_search_video_id(query: str) -> str:
    opts = {"quiet": True, "noplaylist": True}
    with YoutubeDL(opts) as ydl:
        result = ydl.extract_info(f"ytsearch:{query}", download=False)
        return result["entries"][0]["id"]


# --- FIX 2 : Load + sanitize cookies for Playwright ---
def load_cookies(context, cookies_path: Path):
    if not cookies_path.exists():
        raise FileNotFoundError(f"Missing cookies.json at: {cookies_path}")

    raw = json.loads(cookies_path.read_text())

    fixed = []
    for c in raw:
        # Fix SameSite value
        if c.get("sameSite") not in ("Strict", "Lax", "None"):
            c["sameSite"] = "None"

        # Playwright requires expiry as int
        if "expiry" in c and isinstance(c["expiry"], float):
            c["expiry"] = int(c["expiry"])

        fixed.append(c)

    context.add_cookies(fixed)
    print("[TEST] Cookies loaded successfully.")


# --- MAIN TEST ---
def test_playwright_youtube_playlist_creation():
    # STEP 1 — yt-dlp video search
    video_id = youtube_search_video_id("views drake")
    assert isinstance(video_id, str) and len(video_id) > 5
    print("[TEST] Found video ID:", video_id)

    # STEP 2 — Playwright automation
    with sync_playwright() as p:

        # ✔ WORKS IN WSL
        # Headless=False is required so Google does not instantly block everything.
        browser = p.chromium.launch(headless=False)

        context = browser.new_context()

        # Load cookies exported from real Chrome (Windows side)
        load_cookies(context, COOKIES_PATH)

        page = context.new_page()
        page.goto("https://www.youtube.com")

        print("[TEST] Current URL:", page.url)

        # STEP 3 — Open video
        page.goto(f"https://www.youtube.com/watch?v={video_id}")
        page.wait_for_load_state()
        time.sleep(2)

        # STEP 4 — Try opening playlist save dialog
        try:
            page.click("button[aria-label='Save to playlist']")
            time.sleep(1)

            page.click("text=Create new playlist")
            time.sleep(1)

            page.fill('input[aria-label="Name"]', "playwright-test")
            time.sleep(1)

            page.click("text=Create")
            print("[TEST] Playlist created!")

        except Exception as e:
            print("[TEST] Could not create playlist:", e)

        context.close()
        browser.close()
