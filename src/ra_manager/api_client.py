import os

import requests
from dotenv import load_dotenv

from .cache import TTL_HASH_LIST, TTL_USER_PROGRESS, load_cached, save_to_cache


class RAClientError(Exception):
    """Raised when the RetroAchievements API returns an error or is unreachable."""


class RAClient:
    def __init__(self):
        load_dotenv()
        self.user = os.getenv("RA_USERNAME")
        self.api_key = os.getenv("RA_API_KEY")
        self.BASE_URL = "https://retroachievements.org/API"

        if not self.api_key or not self.user:
            print("⚠️  Warning: RA_USERNAME or RA_API_KEY missing in .env file.")

    def _get(self, endpoint: str, params: dict) -> list | dict:
        """
        Internal helper for all GET requests.
        Adds auth params, timeout, and unified error handling.
        """
        params = {"u": self.user, "y": self.api_key, **params}
        try:
            response = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            raise RAClientError(f"Request timed out: {endpoint}") from e
        except requests.exceptions.HTTPError as e:
            raise RAClientError(f"HTTP error {response.status_code}: {endpoint}") from e
        except requests.exceptions.RequestException as e:
            raise RAClientError(f"Request failed: {e}") from e

    def get_console_game_hashes(self, console_id: int, force_refresh: bool = False) -> list:
        """
        Fetches every game and its linked hashes for a given console.
        Results are cached for 24 hours. Pass force_refresh=True to bypass.
        """
        cache_key = f"console_{console_id}"

        if not force_refresh:
            cached = load_cached(cache_key, TTL_HASH_LIST)
            if cached is not None:
                print(f"📦 Using cached hash list for console {console_id}.")
                return cached

        print(f"🌐 Fetching hash list for console {console_id} from RA...")
        result = self._get("API_GetGameList.php", {"i": console_id, "h": 1})
        save_to_cache(cache_key, result)
        return result

    def get_user_progress(self, game_id: int, force_refresh: bool = False) -> dict:
        """
        Fetches achievement progress for the configured user on a specific game.
        Returns: {earned, total, points_earned, points_total, is_mastered}
        Results are cached for 1 hour.
        """
        cache_key = f"progress_{game_id}"

        if not force_refresh:
            cached = load_cached(cache_key, TTL_USER_PROGRESS)
            if cached is not None:
                return cached

        data = self._get(
            "API_GetGameInfoAndUserProgress.php",
            {"u": self.user, "g": game_id},
        )

        achievements = data.get("Achievements", {})
        total = len(achievements)
        earned = sum(
            1 for a in achievements.values() if a.get("DateEarned") or a.get("DateEarnedHardcore")
        )
        points_total = sum(a.get("Points", 0) for a in achievements.values())
        points_earned = sum(
            a.get("Points", 0)
            for a in achievements.values()
            if a.get("DateEarned") or a.get("DateEarnedHardcore")
        )

        result = {
            "earned": earned,
            "total": total,
            "points_earned": points_earned,
            "points_total": points_total,
            "is_mastered": total > 0 and earned == total,
        }

        save_to_cache(cache_key, result)
        return result

    def get_user_summary(self, force_refresh: bool = False) -> dict:
        """
        Fetches the user's overall RA profile stats.
        Returns: {points, softcore_points, rank, games_played}
        Results are cached for 1 hour.
        """
        cache_key = f"summary_{self.user}"

        if not force_refresh:
            cached = load_cached(cache_key, TTL_USER_PROGRESS)
            if cached is not None:
                return cached

        data = self._get("API_GetUserSummary.php", {"u": self.user, "g": 0})

        result = {
            "points": data.get("TotalPoints", 0),
            "softcore_points": data.get("TotalSoftcorePoints", 0),
            "rank": data.get("Rank", 0),
            "games_played": data.get("NumGames", 0),
        }

        save_to_cache(cache_key, result)
        return result

    def get_game_hashes(self, game_id: int, force_refresh: bool = False) -> list[dict]:
        """
        Fetches accepted ROM hashes for a specific game to suggest correct dumps.
        Returns:[{'MD5': str, 'Name': str, 'Labels': list, 'PatchUrl': str}]
        """
        cache_key = f"game_hashes_{game_id}"
        if not force_refresh:
            cached = load_cached(cache_key, TTL_HASH_LIST) # Reuse the 24h TTL
            if cached is not None:
                return cached

        result = self._get("API_GetGameHashes.php", {"i": game_id})
        save_to_cache(cache_key, result)
        return result