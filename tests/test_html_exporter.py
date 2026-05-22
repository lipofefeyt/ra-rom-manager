from pathlib import Path

import pandas as pd
import pytest

from src.ra_manager.html_exporter import export_html


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "filename": ["rayman.gba", "pokemon.gba", "metroid.gba", "unknown.gba"],
            "console": ["gba", "gba", "gba", "gba"],
            "md5": [
                "fb20d6009c7400f37581f81ae5b1e917",
                "dfc6fdf38b3c277b6f176cd7c25712c8",
                "6dab0ac88b4e438092c2a90338e51a1b",
                "000000000000000000000000notareal",
            ],
            "ra_title": ["Rayman Advance", "Pokémon LeafGreen", "Metroid Fusion", ""],
            "ra_game_id": [1141, 1448, 2200, None],
            "matched": [True, True, True, False],
            "earned": [15, 73, 0, None],
            "total": [50, 73, 40, None],
            "completion_pct": [30.0, 100.0, 0.0, None],
            "is_mastered": [False, True, False, False],
            "status": ["In Progress (30.0%)", "Mastered 🏆", "Unplayed", "Unmatched"],
            "suggested_title": ["", "", "", "Metroid Fusion"],
            "suggested_filename": ["", "", "", "Metroid Fusion (USA).gba"],
            "suggested_md5": ["", "", "", "aabbccdd"],
            "patch_url": ["", "", "", "https://example.com/patch"],
        }
    )


@pytest.fixture
def sample_summary() -> dict:
    return {"points": 4200, "softcore_points": 300, "rank": 18500, "games_played": 42}


@pytest.fixture
def output_path(tmp_path) -> Path:
    return tmp_path / "ra_collection.html"


class TestHtmlExportCreatesFile:
    def test_creates_html_file(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        assert output_path.exists()

    def test_returns_output_path(self, sample_df, output_path):
        result = export_html(sample_df, output_path=output_path)
        assert result == output_path

    def test_output_is_valid_html(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content


class TestHtmlSummarySection:
    def test_collection_stats_present(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "Total ROMs" in content
        assert "Matched to RA" in content
        assert "Match Rate" in content

    def test_user_profile_shown_when_summary_provided(self, sample_df, sample_summary, output_path):
        export_html(sample_df, user_summary=sample_summary, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "4200" in content  # points
        assert "18500" in content  # rank

    def test_user_profile_absent_when_no_summary(self, sample_df, output_path):
        export_html(sample_df, user_summary=None, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "RA Profile" not in content


class TestHtmlConsoleTables:
    def test_console_section_heading_present(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "GBA" in content

    def test_rom_filename_present(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "rayman.gba" in content
        assert "pokemon.gba" in content

    def test_mastered_row_class_applied(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "row-mastered" in content

    def test_in_progress_row_class_applied(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "row-in-progress" in content

    def test_unmatched_row_class_applied(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "row-unmatched" in content

    def test_boolean_rendered_as_yes_no(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert ">Yes<" in content or ">No<" in content


class TestHtmlUnmatchedSection:
    def test_unmatched_section_present(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "Unmatched ROMs" in content

    def test_patch_url_rendered_as_link(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert 'href="https://example.com/patch"' in content

    def test_suggested_filename_present(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "Metroid Fusion (USA).gba" in content

    def test_all_matched_shows_placeholder(self, sample_df, output_path):
        all_matched = sample_df[sample_df["matched"]].copy().reset_index(drop=True)
        export_html(all_matched, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "All ROMs matched perfectly!" in content


class TestHtmlWantToPlaySection:
    def test_section_heading_present(self, sample_df, output_path):
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "Want to Play" in content

    def test_placeholder_shown_when_no_csv(self, sample_df, output_path, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        export_html(sample_df, output_path=output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "No want_to_play.csv found" in content
