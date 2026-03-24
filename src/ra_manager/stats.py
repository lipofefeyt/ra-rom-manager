import pandas as pd


def get_completion_label(earned: int, total: int) -> str:
    """Returns a human-readable completion status for a game."""
    if total == 0:
        return "No Achievements"
    if earned == 0:
        return "Unplayed"
    if earned == total:
        return "Mastered 🏆"
    percent = (earned / total) * 100
    return f"In Progress ({percent:.1f}%)"


def enrich_with_progress(df: pd.DataFrame, client) -> pd.DataFrame:
    """
    Fetches achievement progress for every matched ROM and adds columns:
        earned          — achievements earned by the user
        total           — total achievements available
        completion_pct  — percentage complete (0.0 to 100.0)
        is_mastered     — True if all achievements earned
        status          — human-readable label
    """
    df = df.copy()

    earned_list = []
    total_list = []
    pct_list = []
    mastered_list = []
    status_list = []

    matched = df["matched"]
    game_ids = df["ra_game_id"]

    for is_matched, game_id in zip(matched, game_ids, strict=True):
        if not is_matched or pd.isna(game_id):
            earned_list.append(None)
            total_list.append(None)
            pct_list.append(None)
            mastered_list.append(False)
            status_list.append("Unmatched")
            continue

        try:
            progress = client.get_user_progress(int(game_id))
            earned = progress["earned"]
            total = progress["total"]
            pct = round((earned / total) * 100, 1) if total > 0 else 0.0

            earned_list.append(earned)
            total_list.append(total)
            pct_list.append(pct)
            mastered_list.append(progress["is_mastered"])
            status_list.append(get_completion_label(earned, total))

        except Exception as e:
            print(f"⚠️  Could not fetch progress for game {game_id}: {e}")
            earned_list.append(None)
            total_list.append(None)
            pct_list.append(None)
            mastered_list.append(False)
            status_list.append("Error")

    df["earned"] = earned_list
    df["total"] = total_list
    df["completion_pct"] = pct_list
    df["is_mastered"] = mastered_list
    df["status"] = status_list

    return df
