def get_completion_label(awarded, total):
    """Calculates if you've mastered, started, or ignored a game."""
    if awarded == 0: return "Unplayed"
    if awarded == total: return "Mastered 🏆"
    percent = (awarded / total) * 100
    return f"In Progress ({percent:.1f}%)"

def add_stats_to_df(df, client):
    """Enriches your CSV with RA progress data."""
    # This maps the logic to every row in your CSV
    df['Status'] = df.apply(lambda row: 
        get_completion_label(
            client.get_game_progress(row.get('GameID', 0))['NumAwarded'],
            client.get_game_progress(row.get('GameID', 0))['NumAchievements']
        ), axis=1)
    return df