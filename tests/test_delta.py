import pandas as pd
import pytest

from src.ra_manager.delta import compute_delta, load_previous_run, print_delta


def _make_df(rows):
    return pd.DataFrame(rows, columns=[
        "ra_game_id", "ra_title", "matched", "is_mastered", "completion_pct",
    ])


class TestComputeDelta:
    def test_newly_mastered_detected(self):
        prev = _make_df([(1, "Rayman", True, False, 80.0)])
        curr = _make_df([(1, "Rayman", True, True, 100.0)])
        delta = compute_delta(prev, curr)
        assert "Rayman" in delta["newly_mastered"]

    def test_already_mastered_not_repeated(self):
        prev = _make_df([(1, "Rayman", True, True, 100.0)])
        curr = _make_df([(1, "Rayman", True, True, 100.0)])
        delta = compute_delta(prev, curr)
        assert delta["newly_mastered"] == []

    def test_progress_gain_detected(self):
        prev = _make_df([(1, "Metroid", True, False, 30.0)])
        curr = _make_df([(1, "Metroid", True, False, 55.0)])
        delta = compute_delta(prev, curr)
        assert len(delta["progress_gains"]) == 1
        title, old, new = delta["progress_gains"][0]
        assert title == "Metroid"
        assert old == pytest.approx(30.0)
        assert new == pytest.approx(55.0)

    def test_no_gain_not_reported(self):
        prev = _make_df([(1, "Metroid", True, False, 55.0)])
        curr = _make_df([(1, "Metroid", True, False, 55.0)])
        delta = compute_delta(prev, curr)
        assert delta["progress_gains"] == []

    def test_newly_matched_detected(self):
        prev = _make_df([(1, "Rayman", True, False, 0.0)])
        curr = _make_df([
            (1, "Rayman", True, False, 0.0),
            (2, "Pokemon", True, False, 0.0),
        ])
        delta = compute_delta(prev, curr)
        assert "Pokemon" in delta["newly_matched"]

    def test_unmatched_rows_excluded(self):
        prev = _make_df([(1, "Rayman", True, False, 80.0)])
        curr = _make_df([
            (1, "Rayman", True, True, 100.0),
            (None, "Unknown", False, False, 0.0),
        ])
        delta = compute_delta(prev, curr)
        assert "Rayman" in delta["newly_mastered"]
        assert len(delta["newly_mastered"]) == 1

    def test_empty_prev_returns_all_as_newly_matched(self):
        prev = _make_df([])
        curr = _make_df([(1, "Rayman", True, False, 0.0)])
        delta = compute_delta(prev, curr)
        assert "Rayman" in delta["newly_matched"]


class TestLoadPreviousRun:
    def test_returns_none_if_file_missing(self, tmp_path):
        result = load_previous_run(tmp_path / "nonexistent.xlsx")
        assert result is None

    def test_returns_none_on_corrupt_file(self, tmp_path):
        bad = tmp_path / "bad.xlsx"
        bad.write_bytes(b"not an xlsx")
        assert load_previous_run(bad) is None


class TestPrintDelta:
    def test_prints_no_changes_when_empty(self, capsys):
        print_delta({"newly_mastered": [], "progress_gains": [], "newly_matched": []})
        assert "No changes" in capsys.readouterr().out

    def test_prints_newly_mastered(self, capsys):
        print_delta({"newly_mastered": ["Rayman"], "progress_gains": [], "newly_matched": []})
        assert "Rayman" in capsys.readouterr().out

    def test_prints_progress_gain(self, capsys):
        print_delta({
            "newly_mastered": [],
            "progress_gains": [("Metroid", 30.0, 55.0)],
            "newly_matched": [],
        })
        out = capsys.readouterr().out
        assert "Metroid" in out
        assert "30.0" in out
        assert "55.0" in out
