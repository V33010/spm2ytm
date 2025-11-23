"""
Cleanup script to remove duplicate songs from a text file.

Usage:
    python scripts/cleanup_songsfile.py
"""

from pathlib import Path


def cleanup_songs_file():
    """Remove duplicate songs from a text file while preserving order."""

    # Step 1: Prompt user for file location
    print("=" * 60)
    print("Song File Cleanup - Remove Duplicates")
    print("=" * 60)

    file_location = input("\nEnter the path to your song file: ").strip()

    # Validate file exists
    file_path = Path(file_location)
    if not file_path.exists():
        print(f"✗ Error: File not found at {file_location}")
        return

    if not file_path.is_file():
        print(f"✗ Error: {file_location} is not a file")
        return

    print(f"✓ Found file: {file_path}")

    # Step 2: Open and read the file
    print(f"\n▶ Reading songs from file...")
    with open(file_path, "r", encoding="utf-8") as f:
        # Step 3: Create list of songs (strip whitespace, skip empty lines)
        temp_list = [line.strip() for line in f if line.strip()]

    original_count = len(temp_list)
    print(f"  Original song count: {original_count}")

    # Step 4: Remove duplicates using set (preserves order with dict.fromkeys)
    # Using dict.fromkeys() instead of set() to preserve original order
    temp_set = list(dict.fromkeys(temp_list))
    unique_count = len(temp_set)
    duplicates_removed = original_count - unique_count

    print(f"  Unique song count: {unique_count}")
    print(f"  Duplicates removed: {duplicates_removed}")

    # Step 5: Save to new file with -unique.txt suffix
    original_stem = file_path.stem  # filename without extension
    output_filename = f"{original_stem}-unique.txt"
    output_path = file_path.parent / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(temp_set))

    print(f"\n✓ Cleaned file saved to: {output_path}")
    print(f"  Location: {output_path.parent}")
    print(f"  Filename: {output_filename}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        cleanup_songs_file()
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
