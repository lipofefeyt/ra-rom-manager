import os

import requests
from dotenv import load_dotenv


class RAClient:
    def __init__(self):
        load_dotenv()
        # Initialize attributes to None first so they always exist
        self.user = os.getenv("RA_USERNAME")
        self.api_key = os.getenv("RA_API_KEY")
        self.BASE_URL = "https://retroachievements.org/API"

        # Safety Check
        if not self.api_key or not self.user:
            print("⚠️ Warning: RA_USERNAME or RA_API_KEY missing in .env file.")

    def get_console_game_hashes(self, console_id):

        """
        Fetches EVERY game and its linked hashes for a specific console.
        GBA Console ID is 4.
        """
        url = f"{self.BASE_URL}/API_GetGameList.php"

        params = {
            "u": self.user,
            "y": self.api_key,
            "i": console_id,
            "h": 1
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json() # This returns a massive list of games
            else:
                print(f"❌ API Error {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return []
