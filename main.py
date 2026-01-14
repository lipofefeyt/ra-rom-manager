import os
import pandas as pd
from src.ra_manager.scanner import ROMScanner
from src.ra_manager.api_client import RAClient
from src.ra_manager.config import get_rom_path

def main():
    print("--- RetroAchievements ROM Manager ---")
    
    # 1. Initialize Components
    scanner = ROMScanner()
    client = RAClient()
    
    # 2. Scan Local ROMs
    print("\n[1/3] Scanning local ROMs...")
    local_roms_df = scanner.scan()
    
    if local_roms_df.empty:
        print("No ROMs found in your configured directory. Check config.py!")
        return

    # 3. Check for API Credentials
    has_api = client.api_key is not None and "get_this_from_ra" not in client.api_key
    
    if not has_api:
        print("\n[2/3] ⚠️ API Key missing. Skipping RA server checks.")
        print("Showing local ROM list only:")
        print(local_roms_df[['filename', 'console', 'md5']])
    else:
        print("\n[2/3] ✅ API Key found. Connecting to RetroAchievements...")
        # Placeholder for the matching logic we will write next
        print("Matching local hashes against RA database...")
        # For now, we'll just display the scan results
        print(local_roms_df[['filename', 'console', 'md5']])

    # 4. Export results (The "Sheet" functionality)
    print("\n[3/3] Saving data to local cache...")
    output_path = "data/rom_report.csv"
    local_roms_df.to_csv(output_path, index=False)
    print(f"Report saved to {output_path}")

if __name__ == "__main__":
    main()
