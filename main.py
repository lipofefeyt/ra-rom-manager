from src.ra_manager.scanner import ROMScanner
from src.ra_manager.api_client import RAClient
from src.ra_manager.matcher import HashMatcher
from src.ra_manager.config import CONSOLES, FOLDER_TO_CONSOLE_ID, get_rom_path


def main():
    print("--- RetroAchievements ROM Manager ---")

    scanner = ROMScanner()
    client = RAClient()
    matcher = HashMatcher()

    # 1. Scan local ROMs
    print("📂 Scanning local ROMs...")
    df = scanner.scan()

    if df.empty:
        print("⚠️  No ROMs found. Check your ROM_PATH in .env.")
        return

    # 2. For each detected console, fetch the RA hash list and match
    detected_consoles = df["console"].str.lower().unique()
    all_matched = []

    for folder_name in detected_consoles:
        console_id = FOLDER_TO_CONSOLE_ID.get(folder_name)
        if console_id is None:
            print(f"⚠️  Unknown console folder '{folder_name}' — skipping.")
            continue

        console_name = CONSOLES[console_id]
        print(f"📥 Fetching RA hash list for {console_name} (ID {console_id})...")

        ra_game_list = client.get_console_game_hashes(console_id)
        if not ra_game_list:
            print(f"❌ No data returned for {console_name} — skipping.")
            continue

        hash_map = matcher.build_map(ra_game_list)
        console_df = df[df["console"].str.lower() == folder_name].copy()
        matched_df = matcher.match(console_df, hash_map)
        all_matched.append(matched_df)

        matched_count = matched_df["matched"].sum()
        print(f"✅ {console_name}: {matched_count}/{len(matched_df)} ROMs matched.")

    if not all_matched:
        print("❌ No consoles could be matched. Check folder names and .env config.")
        return

    # 3. Combine and export
    import pandas as pd
    final_df = pd.concat(all_matched, ignore_index=True)
    final_df.to_csv("data/identified_roms.csv", index=False)

    total_matched = final_df["matched"].sum()
    print(f"\n🎮 Done! {total_matched}/{len(final_df)} ROMs matched across all consoles.")


if __name__ == "__main__":
    main()