import os
import requests
from dotenv import load_dotenv

class RAClient:
    def __init__(self):
        load_dotenv()
        # Initialize attributes to None first so they always exist
        self.user = os.getenv("RA_USERNAME")
        self.api_key = os.getenv("RA_API_KEY")
        self.BASE_URL = "https://retroachievements.org/API/"

        # Safety Check
        if not self.api_key or not self.user:
            print("⚠️ Warning: RA_USERNAME or RA_API_KEY missing in .env file.")