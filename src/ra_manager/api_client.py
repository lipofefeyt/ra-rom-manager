import json
from pathlib import Path

class RAClient:
    def __init__(self, offline=True): 
        self.offline = offline
        self.mock_path = Path("data/mock_ra_data.json")

    def get_mock_data(self):
        with open(self.mock_path, 'r') as f:
            return json.load(f)

    def get_game_progress(self, game_id):
        if self.offline:
            data = self.get_mock_data()
            # Return the fake stats for the game if they exist
            return data.get(str(game_id), {"NumAwarded": 0, "NumAchievements": 1})
        # ... your real requests.get code stays here for when you land ...