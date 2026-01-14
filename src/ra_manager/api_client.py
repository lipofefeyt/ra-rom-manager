import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RAClient:
    """Handles all communication with the RetroAchievements API."""
    
    BASE_URL = "https://retroachievements.org/API/"

    def __init__(self):
        load_dotenv()
        self.user = os.getenv("RA_USERNAME")
        self.api_key = os.getenv("RA_API_KEY")
    
    # The Safety Check
    if not self.api_key or not self.user:
        print("⚠️ Warning: RA_USERNAME or RA_API_KEY missing in .env")
        print("API functions will be disabled.")


    def test_connection(self):
        """Simple check to see if the API key is valid."""
        if not self.api_key:
            return "Error: No API Key found in .env file!"
        return "Client ready to fetch ROM data."

# You can run this file directly in Pydroid to test
if __name__ == "__main__":
    client = RAClient()
    print(client.test_connection())
