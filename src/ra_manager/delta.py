from pathlib import Path

import pandas as pd


def load_previous_run(xlsx_path: Path) -> pd.DataFrame | None:
    """
    Reads all per-console sheets from a previous workbook and returns a
    combined DataFrame with at minimum ra_game_id, is_mastered, completion_pct.
    Returns None if the file doesn't exist or can't be read.
    """
    if not xlsx_path.exists():
        return None
    try:
        sheets = pd.read_excel(xlsx_path, sheet_name=None, engine="openpyxl")
    except Exception:
        return None

    skip = {"Summary", "Unmatched ROMs", "Want to Play"}
    frames = [df for name, df in sheets.items() if name not in skip and not df.empty]
    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    needed = {"ra_game_id", "is_mastered", "completion_pct", "ra_title", "matched"}
    if not needed.issubset(combined.columns):
        return None
    return combined[list(needed)]


def compute_delta(
    prev: pd.DataFrame,
    curr: pd.DataFrame,
) -> dict:
    """
    Compares two enriched DataFrames (prev / curr) and returns a dict:
      newly_mastered  - list of ra_title newly mastered this run
      progress_gains  - list of (ra_title, old_pct, new_pct) for games that improved
      newly_matched   - list of ra_title that were unmatched before but matched now
    """
    _empty = pd.DataFrame(columns=["ra_game_id", "ra_title", "is_mastered", "completion_pct"])
    _empty_idx = _empty.set_index("ra_game_id")

    prev_matched = prev[prev["matched"]] if not prev.empty else _empty
    curr_matched = curr[curr["matched"]] if not curr.empty else _empty
    prev_idx = prev_matched.set_index("ra_game_id") if not prev_matched.empty else _empty_idx
    curr_idx = curr_matched.set_index("ra_game_id") if not curr_matched.empty else _empty_idx

    newly_mastered = []
    progress_gains = []

    for game_id, curr_row in curr_idx.iterrows():
        if game_id not in prev_idx.index:
            continue
        prev_row = prev_idx.loc[game_id]

        was_mastered = bool(prev_row.get("is_mastered", False))
        is_mastered = bool(curr_row.get("is_mastered", False))
        if not was_mastered and is_mastered:
            newly_mastered.append(curr_row.get("ra_title", str(game_id)))

        old_pct = float(prev_row.get("completion_pct") or 0)
        new_pct = float(curr_row.get("completion_pct") or 0)
        if new_pct > old_pct:
            progress_gains.append((curr_row.get("ra_title", str(game_id)), old_pct, new_pct))

    prev_matched_ids = set(prev_idx.index)
    curr_matched_ids = set(curr_idx.index)
    newly_matched_ids = curr_matched_ids - prev_matched_ids
    newly_matched = list(
        curr_idx.loc[list(newly_matched_ids), "ra_title"]
        if newly_matched_ids else []
    )

    return {
        "newly_mastered": newly_mastered,
        "progress_gains": progress_gains,
        "newly_matched": newly_matched,
    }


def print_delta(delta: dict) -> None:
    """Prints a human-readable delta summary to stdout."""
    if not any(delta.values()):
        print("   No changes since last run.")
        return

    if delta["newly_mastered"]:
        print(f"   🏆 Newly mastered ({len(delta['newly_mastered'])}):")
        for title in delta["newly_mastered"]:
            print(f"      • {title}")

    if delta["newly_matched"]:
        print(f"   🔗 Newly matched ({len(delta['newly_matched'])}):")
        for title in delta["newly_matched"]:
            print(f"      • {title}")

    if delta["progress_gains"]:
        print(f"   📈 Progress gains ({len(delta['progress_gains'])}):")
        for title, old, new in delta["progress_gains"]:
            print(f"      • {title}: {old:.1f}% → {new:.1f}%")
