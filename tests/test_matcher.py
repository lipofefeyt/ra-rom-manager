import json
from pathlib import Path

import pandas as pd
import pytest

from src.ra_manager.matcher import HashMatcher

FIXTURES = Path("tests/fixtures/mock_ra_data.json")


@pytest.fixture
def mock_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.fixture
def matcher():
    return HashMatcher()


@pytest.fixture
def game_list(mock_data):
    return mock_data["console_4_games"]


class TestBuildMap:
    def test_builds_map_from_list_hashes(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        assert "fb20d6009c7400f37581f81ae5b1e917" in hash_map

    def test_maps_hash_to_title_and_id(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        title, game_id = hash_map["fb20d6009c7400f37581f81ae5b1e917"]
        assert title == "Rayman Advance"
        assert game_id == 1141

    def test_game_with_multiple_hashes(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        assert "dfc6fdf38b3c277b6f176cd7c25712c8" in hash_map
        assert hash_map["dfc6fdf38b3c277b6f176cd7c25712c8"][1] == 1448

    def test_empty_game_list_returns_empty_map(self, matcher):
        assert matcher.build_map([]) == {}

    def test_handles_string_hash(self, matcher):
        game_list = [{"ID": 99, "Title": "Test Game", "Hashes": "aabbccdd"}]
        hash_map = matcher.build_map(game_list)
        assert "aabbccdd" in hash_map

    def test_normalises_hash_to_lowercase(self, matcher):
        game_list = [{"ID": 1, "Title": "Test", "Hashes": ["ABCDEF1234567890ABCDEF1234567890"]}]
        hash_map = matcher.build_map(game_list)
        assert "abcdef1234567890abcdef1234567890" in hash_map

    def test_skips_empty_hash_strings(self, matcher):
        game_list = [{"ID": 1, "Title": "Test", "Hashes": ["", "  ", "validhash"]}]
        hash_map = matcher.build_map(game_list)
        assert "" not in hash_map
        assert "  " not in hash_map
        assert "validhash" in hash_map


class TestMatch:
    def _make_df(self, md5s: list[str]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "filename": [f"game_{i}.gba" for i in range(len(md5s))],
                "md5": md5s,
                "console": ["gba"] * len(md5s),
            }
        )

    def test_matched_rom_has_correct_title(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["fb20d6009c7400f37581f81ae5b1e917"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["ra_title"] == "Rayman Advance"

    def test_matched_rom_has_correct_game_id(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["fb20d6009c7400f37581f81ae5b1e917"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["ra_game_id"] == 1141

    def test_matched_rom_sets_matched_true(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["fb20d6009c7400f37581f81ae5b1e917"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["matched"]

    def test_unmatched_rom_gets_unknown_title(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["000000000000000000000000notareal"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["ra_title"] == "Unknown/Unlinked"

    def test_unmatched_rom_sets_matched_false(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["000000000000000000000000notareal"])
        result = matcher.match(df, hash_map)
        assert not result.iloc[0]["matched"]

    def test_unmatched_rom_has_no_game_id(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["000000000000000000000000notareal"])
        result = matcher.match(df, hash_map)
        assert pd.isna(result.iloc[0]["ra_game_id"])

    def test_mixed_matched_and_unmatched(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(
            [
                "fb20d6009c7400f37581f81ae5b1e917",  # matches Rayman
                "000000000000000000000000notareal",  # no match
            ]
        )
        result = matcher.match(df, hash_map)
        assert result["matched"].sum() == 1
        assert len(result) == 2

    def test_md5_normalised_before_matching(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["  FB20D6009C7400F37581F81AE5B1E917  "])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["matched"]

    def test_original_df_not_mutated(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["fb20d6009c7400f37581f81ae5b1e917"])
        original_cols = set(df.columns)
        matcher.match(df, hash_map)
        assert set(df.columns) == original_cols


class TestEnrichWithDumpHints:
    def _matched_df(self, game_list, matcher) -> pd.DataFrame:
        hash_map = matcher.build_map(game_list)
        df = pd.DataFrame(
            {
                # Row 0 matched by MD5; Row 1 unmatched but title fuzzy-matches "Metroid Fusion"
                "filename": ["Rayman_Advance.gba", "Metroid_Fusion_v1.1.gba"],
                "md5": ["fb20d6009c7400f37581f81ae5b1e917", "000000000000000000000000notareal"],
                "console": ["gba", "gba"],
            }
        )
        return matcher.match(df, hash_map)

    def _make_client(self, hash_list=None):
        client = type("Client", (), {})()
        client.get_game_hashes = lambda game_id, **kw: hash_list or []
        return client

    def test_returns_df_unchanged_when_all_matched(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = pd.DataFrame(
            {
                "filename": ["Rayman_Advance.gba"],
                "md5": ["fb20d6009c7400f37581f81ae5b1e917"],
                "console": ["gba"],
            }
        )
        matched = matcher.match(df, hash_map)
        result = matcher.enrich_with_dump_hints(matched, game_list, self._make_client())
        assert list(result["filename"]) == list(matched["filename"])

    def test_adds_suggestion_columns_for_unmatched_roms(self, matcher, game_list):
        client = self._make_client(
            hash_list=[{"Name": "Metroid Fusion (USA).gba", "MD5": "aabbccdd", "PatchUrl": None}]
        )
        matched = self._matched_df(game_list, matcher)
        result = matcher.enrich_with_dump_hints(matched, game_list, client)

        unmatched_row = result[~result["matched"]].iloc[0]
        assert unmatched_row["suggested_title"] == "Metroid Fusion"
        assert unmatched_row["suggested_filename"] == "Metroid Fusion (USA).gba"

    def test_handles_empty_api_hashes_gracefully(self, matcher, game_list):
        client = self._make_client(hash_list=[])
        matched = self._matched_df(game_list, matcher)
        result = matcher.enrich_with_dump_hints(matched, game_list, client)

        unmatched_row = result[~result["matched"]].iloc[0]
        val = unmatched_row.get("suggested_filename")
        assert pd.isna(val) or val in (None, "")

    def test_matched_rows_not_affected(self, matcher, game_list):
        client = self._make_client(hash_list=[])
        matched = self._matched_df(game_list, matcher)
        result = matcher.enrich_with_dump_hints(matched, game_list, client)

        matched_row = result[result["matched"]].iloc[0]
        assert matched_row["ra_title"] == "Rayman Advance"


class TestSuggestMatches:
    def test_finds_close_title(self, matcher, game_list):
        # Provide an unmatched dataframe with a slightly misspelled/modified filename
        df = pd.DataFrame({"filename": ["Rayman_Advance_USA.gba"]})
        result = matcher.suggest_matches(df, game_list)

        assert result.iloc[0]["suggested_title"] == "Rayman Advance"
        assert result.iloc[0]["suggested_game_id"] == 1141

    def test_returns_none_on_garbage_filename(self, matcher, game_list):
        df = pd.DataFrame({"filename": ["hjksdfhjk.gba"]})
        result = matcher.suggest_matches(df, game_list)

        is_none = result.iloc[0]["suggested_title"] is None
        assert pd.isna(result.iloc[0]["suggested_title"]) or is_none
