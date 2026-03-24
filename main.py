import pandas as pd

from src.ra_manager.api_client import RAClient, RAClientError
from src.ra_manager.config import CONSOLES, FOLDER_TO_CONSOLE_ID
from src.ra_manager.exporter import export
from src.ra_manager.matcher import HashMatcher
from src.ra_manager.scanner import ROMScanner
from src.ra_manager.stats import enrich_with_progress


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

        try:
            ra_game_list = client.get_console_game_hashes(console_id)
        except RAClientError as e:
            print(f"❌ {console_name}: {e} — skipping.")
            continue

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

    final_df = pd.concat(all_matched, ignore_index=True)

    # 3. Fetch achievement progress for all matched ROMs
    matched_count = final_df["matched"].sum()
    print(f"\n🏆 Fetching achievement progress for {matched_count} matched ROMs...")
    final_df = enrich_with_progress(final_df, client)

    # 4. Fetch user summary for the Summary sheet
    user_summary = None
    try:
        user_summary = client.get_user_summary()
    except RAClientError as e:
        print(f"⚠️  Could not fetch user summary: {e}")

    # 5. Print summary
    mastered = final_df["is_mastered"].sum()
    in_progress = final_df["status"].str.startswith("In Progress").sum()
    unplayed = (final_df["status"] == "Unplayed").sum()

    print("\n📊 Summary:")
    print(f"   Total ROMs    : {len(final_df)}")
    print(f"   Matched       : {final_df['matched'].sum()}")
    print(f"   Mastered 🏆   : {mastered}")
    print(f"   In Progress   : {in_progress}")
    print(f"   Unplayed      : {unplayed}")

    # 6. Export to Excel
    output_path = export(final_df, user_summary)
    print(f"\n💾 Saved to {output_path}")


if __name__ == "__main__":
    main()
