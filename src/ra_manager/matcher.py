import difflib
import re

import pandas as pd


class HashMatcher:
    """Builds a hash → RA game lookup and matches it against a scanned ROM DataFrame."""

    def normalize(self, name: str) -> str:
        """
        Aggressively cleans a title for comparison.
        Lives as a staticmethod so it can be called via self.normalize.
        """
        # 1. Remove brackets and parentheses e.g., (Europe) or [!]
        n = re.sub(r"\(.*?\)|\[.*?\]", "", name)
        
        # 2. Remove "The" as a standalone word (at start, end, or middle)
        # This handles "The Legend of Zelda" and "Legend of Zelda, The"
        n = re.sub(r"\bthe\b", "", n, flags=re.IGNORECASE)
        
        # 3. Strip all non-alphanumeric chars EXCEPT spaces
        # We keep spaces so titles like "God of War" and "God of War II" stay distinct
        n = n.lower().strip()
        n = re.sub(r"[^a-z0-9\s]", "", n)

        # 4. Clean up double spaces and return
        return " ".join(n.split())

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
                    if h and h.strip():
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
        df["ra_title"] = df["md5"].map(lambda h: hash_map.get(h, (None, None))[0])
        df["ra_game_id"] = df["md5"].map(lambda h: hash_map.get(h, (None, None))[1])
        df["matched"] = df["ra_title"].notna()
        df["ra_title"] = df["ra_title"].fillna("Unknown/Unlinked")

        return df

    def suggest_matches(self, unmatched_df: pd.DataFrame, ra_game_list: list) -> pd.DataFrame:
        df = unmatched_df.copy()

        # 1. Map original RA titles to their Game IDs
        title_to_id = {g.get("Title"): g.get("ID") for g in ra_game_list if g.get("Title")}

        # 2. Create a dictionary of {normalized_title: original_title}
        # Note the use of self.normalize here!
        norm_to_orig = {self.normalize(title): title for title in title_to_id.keys()}
        known_norms = list(norm_to_orig.keys())

        suggested_ids = []
        suggested_titles = []

        for filename in df["filename"]:
            clean_name = filename.rsplit(".", 1)[0]
            
            # Use self.normalize here too!
            norm_query = self.normalize(clean_name)

            # Match using a 0.6 cutoff for better accuracy (less "Dragon Lore" errors)
            matches = difflib.get_close_matches(norm_query, known_norms, n=1, cutoff=0.6)

            if matches:
                orig_title = norm_to_orig[matches[0]]
                suggested_titles.append(orig_title)
                suggested_ids.append(title_to_id[orig_title])
            else:
                suggested_titles.append(None)
                suggested_ids.append(None)

        df["suggested_title"] = suggested_titles
        df["suggested_game_id"] = suggested_ids
        return df

