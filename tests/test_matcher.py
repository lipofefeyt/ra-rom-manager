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
        assert "abc123def456abc123def456abc123de" in hash_map

    def test_maps_hash_to_title_and_id(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        title, game_id = hash_map["abc123def456abc123def456abc123de"]
        assert title == "Rayman Advance"
        assert game_id == 1141

    def test_game_with_multiple_hashes(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        assert "deadbeefdeadbeefdeadbeefdeadbeef" in hash_map
        assert "cafecafecafecafecafecafecafecafe" in hash_map
        # Both hashes map to the same game
        assert hash_map["deadbeefdeadbeefdeadbeefdeadbeef"][1] == 1448
        assert hash_map["cafecafecafecafecafecafecafecafe"][1] == 1448

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
        return pd.DataFrame({
            "filename": [f"game_{i}.gba" for i in range(len(md5s))],
            "md5": md5s,
            "console": ["gba"] * len(md5s),
        })

    def test_matched_rom_has_correct_title(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["abc123def456abc123def456abc123de"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["ra_title"] == "Rayman Advance"

    def test_matched_rom_has_correct_game_id(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["abc123def456abc123def456abc123de"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["ra_game_id"] == 1141

    def test_matched_rom_sets_matched_true(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["abc123def456abc123def456abc123de"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["matched"] is True

    def test_unmatched_rom_gets_unknown_title(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["000000000000000000000000notareal"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["ra_title"] == "Unknown/Unlinked"

    def test_unmatched_rom_sets_matched_false(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["000000000000000000000000notareal"])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["matched"] is False

    def test_unmatched_rom_has_no_game_id(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["000000000000000000000000notareal"])
        result = matcher.match(df, hash_map)
        assert pd.isna(result.iloc[0]["ra_game_id"])

    def test_mixed_matched_and_unmatched(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df([
            "abc123def456abc123def456abc123de",  # matches Rayman
            "000000000000000000000000notareal",  # no match
        ])
        result = matcher.match(df, hash_map)
        assert result["matched"].sum() == 1
        assert len(result) == 2

    def test_md5_normalised_before_matching(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["  ABC123DEF456ABC123DEF456ABC123DE  "])
        result = matcher.match(df, hash_map)
        assert result.iloc[0]["matched"] is True

    def test_original_df_not_mutated(self, matcher, game_list):
        hash_map = matcher.build_map(game_list)
        df = self._make_df(["abc123def456abc123def456abc123de"])
        original_cols = set(df.columns)
        matcher.match(df, hash_map)
        assert set(df.columns) == original_cols