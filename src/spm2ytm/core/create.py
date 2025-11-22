import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def load_cookies(context, cookies_file_path: str):
    """Load cookies.json into Playwright browser context."""
    with open(cookies_file_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)


def create_youtube_playlist(playlist_name: str, cookies_path: str):
    """Create a new playlist on YouTube and return its playlist ID."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        load_cookies(context, cookies_path)

        page = context.new_page()
        page.goto("https://www.youtube.com")

        # Open create menu
        page.click("button[aria-label='Create']")

        # Click "Create playlist"
        page.click("yt-formatted-string:has-text('Create playlist')")

        # Enter playlist name
        page.fill("input#input-1", playlist_name)

        # Confirm creation
        page.click("button:has-text('Create')")

        time.sleep(2)

        # After creating, we get redirected → grab playlist ID from URL
        url = page.url
        # e.g., https://www.youtube.com/playlist?list=PLxZ...
        playlist_id = url.split("list=")[-1]

        browser.close()
        return playlist_id


def add_video_to_playlist(video_id: str, playlist_id: str, cookies_path: str):
    """Add a single video to a playlist using the video page menu."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        load_cookies(context, cookies_path)
        page = context.new_page()

        page.goto(f"https://www.youtube.com/watch?v={video_id}")
        page.wait_for_selector("button[aria-label='Save to playlist']")

        # Click save button
        page.click("button[aria-label='Save to playlist']")

        # Select the playlist checkmark box
        page.click(f"tp-yt-paper-checkbox[playlist-id='{playlist_id}']")

        # Close the menu
        page.keyboard.press("Escape")

        browser.close()


def process_id_file(video_id_file: str, cookies_path: str, playlist_name: str):
    """Main function that creates a playlist and adds all videos to it."""
    video_ids = []
    with open(video_id_file, "r", encoding="utf-8") as f:
        for line in f:
            clean = line.strip()
            if clean:
                video_ids.append(clean)

    print(f"[+] Creating YouTube playlist: {playlist_name}")
    playlist_id = create_youtube_playlist(playlist_name, cookies_path)
    print(f"[+] Playlist created with ID: {playlist_id}")

    print(f"[+] Adding {len(video_ids)} videos...")
    for vid in video_ids:
        print(f"  → Adding {vid}")
        add_video_to_playlist(vid, playlist_id, cookies_path)

    print("[+] Done! Playlist created and all videos added.")
