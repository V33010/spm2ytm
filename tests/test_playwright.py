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
        if c.get("sameSite") not in ("Strict", "Lax", "None"):
            c["sameSite"] = "None"
        if "expires" in c:
            if c["expires"] is None:
                del c["expires"]
            elif isinstance(c["expires"], float):
                c["expires"] = int(c["expires"])
        if "expiry" in c:
            if c["expiry"] is None:
                del c["expiry"]
            elif isinstance(c["expiry"], float):
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

    # Target playlist name
    playlist_name = "new sound old"

    # STEP 2 — Playwright automation
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        load_cookies(context, COOKIES_PATH)

        page = context.new_page()

        page.goto("https://www.youtube.com")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if page.locator("button:has-text('Sign in')").is_visible():
            print("[TEST] WARNING: Not logged in! Cookies may be invalid.")
            page.screenshot(path="debug_not_logged_in.png")
            context.close()
            browser.close()
            return

        print("[TEST] Logged in successfully")
        print("[TEST] Current URL:", page.url)

        # STEP 3 — Open video
        page.goto(f"https://www.youtube.com/watch?v={video_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # STEP 4 — Add to playlist
        try:
            # Click the 3-dot menu button
            three_dot_menu = page.locator(
                "button.yt-spec-button-shape-next[aria-label='More actions']"
            ).first
            three_dot_menu.wait_for(state="visible", timeout=10000)
            three_dot_menu.click()
            print("[TEST] Clicked 3-dot menu")
            time.sleep(1)

            # Click "Save" from the dropdown menu
            save_option = page.locator(
                "ytd-menu-service-item-renderer:has-text('Save')"
            ).first
            save_option.wait_for(state="visible", timeout=5000)
            save_option.click()
            print("[TEST] Clicked Save option")
            time.sleep(2)

            # Click on the playlist using aria-label which contains the playlist name
            # Format is: "playlist_name, Private, Not selected" or "playlist_name, Private, Selected"
            playlist_item = page.locator(
                f"yt-list-item-view-model[aria-label^='{playlist_name},']"
            ).first
            playlist_item.wait_for(state="visible", timeout=5000)
            playlist_item.click()
            print(f"[TEST] Added to playlist: {playlist_name}")
            time.sleep(1)

            # Close the dialog
            page.keyboard.press("Escape")
            print("[TEST] Done!")

        except Exception as e:
            print("[TEST] Could not add to playlist:", e)
            page.screenshot(path="debug_screenshot.png")
            print("[TEST] Screenshot saved to debug_screenshot.png")

        time.sleep(2)
        context.close()
        browser.close()
