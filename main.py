import argparse
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.ra_manager.api_client import RAClient, RAClientError
from src.ra_manager.cache import clear_all, record_run
from src.ra_manager.config import CONSOLES, FOLDER_TO_CONSOLE_ID
from src.ra_manager.dashboard import serve as serve_dashboard
from src.ra_manager.delta import compute_delta, load_previous_run, print_delta
from src.ra_manager.exporter import export
from src.ra_manager.franchise import run_franchise_report
from src.ra_manager.html_exporter import export_html
from src.ra_manager.matcher import HashMatcher
from src.ra_manager.patcher import apply_patches
from src.ra_manager.renamer import rename_roms
from src.ra_manager.scanner import ROMScanner
from src.ra_manager.stats import enrich_with_progress


def _run_for_user(args, client: RAClient, out_stem: str) -> None:
    """Runs the full scan → match → enrich → export flow for one user."""
    scanner = ROMScanner(exclude_dirs=args.exclude)
    matcher = HashMatcher()

    print("📂 Scanning local ROMs...")
    df = scanner.scan()

    if df.empty:
        print("⚠️  No ROMs found. Check your ROM_PATH in .env.")
        return

    detected_consoles = df["console"].str.lower().unique()

    if args.console:
        requested = args.console.lower()
        if requested not in FOLDER_TO_CONSOLE_ID:
            valid = ", ".join(sorted(FOLDER_TO_CONSOLE_ID.keys()))
            print(f"❌ Unknown console '{requested}'. Valid options: {valid}")
            return
        detected_consoles = [requested]

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
        matched_df = matcher.enrich_with_dump_hints(matched_df, ra_game_list, client)
        all_matched.append(matched_df)

        matched_count = matched_df["matched"].sum()
        print(f"✅ {console_name}: {matched_count}/{len(matched_df)} ROMs matched.")

    if not all_matched:
        print("❌ No consoles could be matched. Check folder names and .env config.")
        return

    final_df = pd.concat(all_matched, ignore_index=True)

    user_summary = None
    if args.hint:
        print("\nℹ️  Hint mode: skipping achievement progress fetch.")
    else:
        matched_count = final_df["matched"].sum()
        print(f"\n🏆 Fetching achievement progress for {matched_count} matched ROMs...")
        final_df = enrich_with_progress(final_df, client)

        try:
            user_summary = client.get_user_summary()
        except RAClientError as e:
            print(f"⚠️  Could not fetch user summary: {e}")

    mastered = final_df["is_mastered"].sum()
    in_progress = final_df["status"].str.startswith("In Progress").sum()
    unplayed = (final_df["status"] == "Unplayed").sum()

    print("\n📊 Summary:")
    print(f"   Total ROMs    : {len(final_df)}")
    print(f"   Matched       : {final_df['matched'].sum()}")
    print(f"   Mastered 🏆   : {mastered}")
    print(f"   In Progress   : {in_progress}")
    print(f"   Unplayed      : {unplayed}")

    if not args.hint:
        record_run(len(final_df), int(final_df["matched"].sum()), int(mastered))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if args.timestamp else ""
    base_xlsx = Path("data") / f"{out_stem}.xlsx"

    if args.csv:
        csv_name = f"{out_stem}_{timestamp}.csv" if timestamp else f"{out_stem}.csv"
        out_path = Path("data") / csv_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(out_path, index=False)
        print(f"\n💾 Saved plain CSV to {out_path}")
    else:
        xlsx_name = f"{out_stem}_{timestamp}.xlsx" if timestamp else f"{out_stem}.xlsx"
        out_path = Path("data") / xlsx_name
        prev_run = load_previous_run(base_xlsx) if not args.hint else None
        export(final_df, user_summary, output_path=out_path, client=client)
        print(f"\n💾 Saved Excel workbook to {out_path}")

        if prev_run is not None and not args.hint:
            print("\n📊 Changes since last run:")
            print_delta(compute_delta(prev_run, final_df))

    if args.html:
        html_name = f"{out_stem}_{timestamp}.html" if timestamp else f"{out_stem}.html"
        html_path = Path("data") / html_name
        export_html(final_df, user_summary, output_path=html_path)
        print(f"🌐 Saved HTML report to {html_path}")

    if args.patch:
        print("\n🩹 Applying patches for unmatched ROMs...")
        apply_patches(final_df, dry_run=args.dry_run)

    if args.rename or args.dry_run:
        label = "Previewing rename (dry-run)" if args.dry_run else "Auto-Renaming Matched ROMs"
        print(f"\n🏷️  {label}...")
        rename_roms(final_df, dry_run=args.dry_run)


def main():
    parser = argparse.ArgumentParser(description="RetroAchievements ROM Manager")
    parser.add_argument("--rename", action="store_true", help="Auto-rename perfectly matched ROMs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview --rename changes without touching the filesystem",
    )
    parser.add_argument("--exclude", nargs="+", default=list(), help="Folders to skip")
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Add a timestamp to the output file so it doesn't overwrite",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output a plain CSV file instead of Excel",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Output an HTML report in addition to Excel",
    )
    parser.add_argument(
        "--franchise",
        type=str,
        help="Search RA for a franchise (e.g., 'Pokemon') and generate a progress report",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Clear the local cache and fetch fresh data",
    )
    parser.add_argument(
        "--console",
        type=str,
        metavar="FOLDER",
        help="Only process one console folder (e.g. gba, snes, psx)",
    )
    parser.add_argument(
        "--hint",
        action="store_true",
        help="Sourcing-only run: match ROMs and suggest correct dumps, skip progress fetch",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Download and apply xdelta3 patches for unmatched ROMs that have a patch URL",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start local web dashboard on http://127.0.0.1:5000",
    )
    parser.add_argument(
        "--user",
        type=str,
        metavar="USERNAME",
        help="Override RA_USERNAME for this run (single user)",
    )

    args = parser.parse_args()

    if args.serve:
        serve_dashboard()
        return

    print("--- RetroAchievements ROM Manager ---")

    if args.refresh:
        print("♻️  Clearing local cache...")
        clear_all()
        print("🗑️  Cache cleared.")

    # Determine which users to process
    users_env = os.getenv("RA_USERS", "")
    if args.user:
        usernames = [args.user]
    elif users_env:
        usernames = [u.strip() for u in users_env.split(",") if u.strip()]
    else:
        usernames = [None]  # None → use RA_USERNAME from env

    for username in usernames:
        client = RAClient(user=username)

        if len(usernames) > 1:
            print(f"\n{'='*40}\n👤 Processing user: {username}\n{'='*40}")

        if args.franchise:
            print("--- RetroAchievements Franchise Planner ---")
            run_franchise_report(args.franchise, client)
            continue

        out_stem = f"ra_collection_{username}" if username else "ra_collection"
        _run_for_user(args, client, out_stem)


if __name__ == "__main__":
    main()
