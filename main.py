import os
import time
import pandas as pd
from src.ra_manager.scanner import ROMScanner
from src.ra_manager.api_client import RAClient
from src.ra_manager.config import get_rom_path

def main():
    print("--- RetroAchievements ROM Manager ---")
    
    # 1. Initialize Components
    scanner = ROMScanner()
    client = RAClient()
    
    # 1. Get the RA "Master List" for GBA (ID 4)
    print("📥 Downloading GBA Master Hash List from RetroAchievements...")
    ra_master_list = client.get_console_game_hashes(5)
    
    # 1. Create a robust lookup dictionary
    hash_map = {}
    print(f"Parsing {len(ra_master_list)} games from RA...")

    for game in ra_master_list:
        title = game.get('Title', 'Unknown')
        hashes = game.get('Hashes', [])
        
        # RetroAchievements sometimes sends Hashes as a list, sometimes a string
        if isinstance(hashes, list):
            for h in hashes:
                if h: 
                    print(f"'{h}' ===> '{title}'")

                    hash_map[str(h).lower().strip()] = title
        elif isinstance(hashes, str) and hashes:
            # If it's a single string, clean and add it
            hash_map[hashes.lower().strip()] = title

    # 2. Match with your Local Scanned Data
    print(f"📂 Scanning local ROMs...")
    df = scanner.scan()
    
    # Ensure local MD5s are clean strings for the comparison
    df['md5'] = df['md5'].astype(str).str.lower().str.strip()
    
    # 3. Use a direct lookup to avoid mapping errors
    df['ra_title'] = df['md5'].map(hash_map).fillna("Unknown/Unlinked")
    
    # 4. Save
    df.to_csv("data/identified_roms.csv", index=False)
    
    matched_count = len(df[df['ra_title'] != "Unknown/Unlinked"])
    print(f"✅ Done! Matched {matched_count} out of {len(df)} games.")

if __name__ == "__main__":
    main()
