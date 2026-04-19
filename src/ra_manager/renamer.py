import re
from pathlib import Path

import pandas as pd


def sanitize_filename(name: str) -> str:
    """
    Removes or replaces characters that are illegal in Windows/Linux file systems.
    Replaces colons with a dash to keep subtitles readable.
    """
    # Replace colons with dashes (e.g., "Game: Subtitle" -> "Game - Subtitle")
    clean = name.replace(":", " -")
    # Remove other illegal characters: \ / * ? " < > |
    clean = re.sub(r'[\\/*?"<>|]', "", clean)
    # Clean up any accidental double spaces
    return " ".join(clean.split())


def rename_roms(df: pd.DataFrame) -> None:
    """
    Safely renames perfectly matched ROMs to their official RA titles.
    """
    # LAYER 1 SAFETY: Only process perfectly matched ROMs
    matched_df = df[df["matched"]]

    if matched_df.empty:
        print("   ⚠️  No perfectly matched ROMs found to rename.")
        return

    renamed_count = 0
    for _, row in matched_df.iterrows():
        old_path = Path(row["path"])

        # Ensure the file actually exists on disk
        if not old_path.exists():
            continue

        # LAYER 2 SAFETY: Sanitize the official RA title
        ra_title = str(row["ra_title"])
        safe_title = sanitize_filename(ra_title)

        # Keep the exact same file extension (.zip, .iso, .chd)
        extension = old_path.suffix
        new_name = f"{safe_title}{extension}"
        new_path = old_path.parent / new_name

        # If the name is already perfect, do nothing
        if old_path == new_path:
            continue

        # LAYER 3 SAFETY: Don't overwrite an existing file
        if new_path.exists():
            print(f"   ⚠️  Skipping: '{new_name}' already exists in that folder.")
        else:
            old_path.rename(new_path)
            print(f"   ✅ Renamed: '{old_path.name}'  ->  '{new_name}'")
            renamed_count += 1

    print(f"\n   📝 Successfully renamed {renamed_count} files.")
