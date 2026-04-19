from unittest.mock import MagicMock

import pandas as pd

from src.ra_manager.stats import enrich_with_progress, get_completion_label


class TestGetCompletionLabel:
    def test_unplayed(self):
        assert get_completion_label(0, 50) == "Unplayed"

    def test_mastered(self):
        assert get_completion_label(50, 50) == "Mastered 🏆"

    def test_in_progress(self):
        assert get_completion_label(25, 50) == "In Progress (50.0%)"

    def test_no_achievements(self):
        assert get_completion_label(0, 0) == "No Achievements"

    def test_nearly_mastered(self):
        label = get_completion_label(49, 50)
        assert label.startswith("In Progress")
        assert "98.0%" in label


class TestEnrichWithProgress:
    def _make_df(self, matched: list[bool], game_ids: list) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "filename": [f"game_{i}.gba" for i in range(len(matched))],
                "matched": matched,
                "ra_game_id": game_ids,
            }
        )

    def _mock_client(self, progress: dict) -> MagicMock:
        client = MagicMock()
        client.get_user_progress.return_value = progress
        return client

    def test_matched_rom_gets_progress_columns(self):
        df = self._make_df([True], [1141])
        client = self._mock_client(
            {
                "earned": 15,
                "total": 50,
                "points_earned": 120,
                "points_total": 400,
                "is_mastered": False,
            }
        )
        result = enrich_with_progress(df, client)
        assert result.iloc[0]["earned"] == 15
        assert result.iloc[0]["total"] == 50
        assert result.iloc[0]["completion_pct"] == 30.0

    def test_mastered_rom_flagged_correctly(self):
        df = self._make_df([True], [1448])
        client = self._mock_client(
            {
                "earned": 73,
                "total": 73,
                "points_earned": 580,
                "points_total": 580,
                "is_mastered": True,
            }
        )
        result = enrich_with_progress(df, client)
        assert result.iloc[0]["is_mastered"]
        assert result.iloc[0]["status"] == "Mastered 🏆"

    def test_unmatched_rom_gets_unmatched_status(self):
        df = self._make_df([False], [None])
        client = MagicMock()
        result = enrich_with_progress(df, client)
        assert result.iloc[0]["status"] == "Unmatched"
        client.get_user_progress.assert_not_called()

    def test_api_error_sets_error_status(self):
        df = self._make_df([True], [9999])
        client = MagicMock()
        client.get_user_progress.side_effect = Exception("API down")
        result = enrich_with_progress(df, client)
        assert result.iloc[0]["status"] == "Error"

    def test_original_df_not_mutated(self):
        df = self._make_df([True], [1141])
        client = self._mock_client(
            {
                "earned": 10,
                "total": 20,
                "points_earned": 50,
                "points_total": 100,
                "is_mastered": False,
            }
        )
        original_cols = set(df.columns)
        enrich_with_progress(df, client)
        assert set(df.columns) == original_cols

    def test_mixed_matched_and_unmatched(self):
        df = self._make_df([True, False, True], [1141, None, 2200])
        client = self._mock_client(
            {
                "earned": 5,
                "total": 10,
                "points_earned": 50,
                "points_total": 100,
                "is_mastered": False,
            }
        )
        result = enrich_with_progress(df, client)
        assert result.iloc[1]["status"] == "Unmatched"
        assert client.get_user_progress.call_count == 2
