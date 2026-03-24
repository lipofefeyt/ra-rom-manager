import pandas as pd


class HashMatcher:
    """Builds a hash → RA game lookup and matches it against a scanned ROM DataFrame."""

    def build_map(self, ra_game_list: list) -> dict:
        """
        Parses the raw RA game list into a flat {md5: (title, game_id)} lookup dict.
        Handles both list and string formats for the Hashes field.
        """
        hash_map = {}

        for game in ra_game_list:
            title = game.get("Title", "Unknown")
            game_id = game.get("ID")
            hashes = game.get("Hashes", [])

            if isinstance(hashes, list):
                for h in hashes:
                    if h:
                        hash_map[h.lower().strip()] = (title, game_id)
            elif isinstance(hashes, str) and hashes:
                hash_map[hashes.lower().strip()] = (title, game_id)

        return hash_map

    def match(self, df: pd.DataFrame, hash_map: dict) -> pd.DataFrame:
        """
        Adds ra_title and ra_game_id columns to the scanned ROM DataFrame
        by looking up each ROM's MD5 in the hash map.
        """
        df = df.copy()
        df["md5"] = df["md5"].astype(str).str.lower().str.strip()

        df["ra_title"] = df["md5"].map(
            lambda h: hash_map.get(h, (None, None))[0]
        )
        df["ra_game_id"] = df["md5"].map(
            lambda h: hash_map.get(h, (None, None))[1]
        )

        df["matched"] = df["ra_title"].notna()
        df["ra_title"] = df["ra_title"].fillna("Unknown/Unlinked")

        return df