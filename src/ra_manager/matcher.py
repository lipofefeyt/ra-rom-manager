import pandas as pd
import difflib
import re


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
        """
        Uses deep string normalization and fuzzy matching to guess the intended game.
        """
        df = unmatched_df.copy()
        
        # 1. Map original RA titles to their Game IDs
        title_to_id = {g.get("Title"): g.get("ID") for g in ra_game_list if g.get("Title")}
        
        def normalize(name: str) -> str:
            """Aggressively cleans a title for comparison."""
            # Remove brackets and parentheses e.g., (Europe) or [!]
            n = re.sub(r'\(.*?\)|\[.*?\]', '', name)
            # Remove the word "The " at the start
            n = re.sub(r'^(?:the\s+)', '', n, flags=re.IGNORECASE)
            # Remove ", The" at the end
            n = re.sub(r'(?:,\s*the)$', '', n, flags=re.IGNORECASE)
            # Remove " the " or " The " in the middle
            n = re.sub(r'(?:\s+the\s+)', ' ', n, flags=re.IGNORECASE)
            # Strip all non-alphanumeric chars (spaces, colons, hyphens) and lowercase
            n = re.sub(r'[^a-z0-9]', '', n.lower())
            return n

        # 2. Create a dictionary of {normalized_title: original_title}
        norm_to_orig = {normalize(title): title for title in title_to_id.keys()}
        known_norms = list(norm_to_orig.keys())

        suggested_ids = []
        suggested_titles = []

        for filename in df["filename"]:
            # Drop the file extension
            clean_name = filename.rsplit('.', 1)[0]
            
            # Normalize the user's filename
            norm_query = normalize(clean_name)
            
            # Match the normalized filename against the normalized RA database
            # Cutoff lowered to 0.4 to catch major spelling mistakes
            matches = difflib.get_close_matches(norm_query, known_norms, n=1, cutoff=0.4)
            
            if matches:
                # We found a match! Get the original beautifully formatted title back
                orig_title = norm_to_orig[matches[0]]
                suggested_titles.append(orig_title)
                suggested_ids.append(title_to_id[orig_title])
            else:
                suggested_titles.append(None)
                suggested_ids.append(None)

        df["suggested_title"] = suggested_titles
        df["suggested_game_id"] = suggested_ids
        return df