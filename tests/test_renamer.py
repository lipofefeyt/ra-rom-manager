from pathlib import Path

import pandas as pd

from src.ra_manager.renamer import rename_roms, sanitize_filename


class TestSanitizeFilename:
    def test_replaces_colon_with_dash(self):
        assert sanitize_filename("Game: Subtitle") == "Game - Subtitle"

    def test_removes_backslash(self):
        assert sanitize_filename("Game\\Name") == "GameName"

    def test_removes_forward_slash(self):
        assert sanitize_filename("Game/Name") == "GameName"

    def test_removes_asterisk(self):
        assert sanitize_filename("Game*Name") == "GameName"

    def test_removes_question_mark(self):
        assert sanitize_filename("Game?Name") == "GameName"

    def test_removes_angle_brackets(self):
        assert sanitize_filename("Game<>Name") == "GameName"

    def test_removes_pipe(self):
        assert sanitize_filename("Game|Name") == "GameName"

    def test_collapses_double_spaces(self):
        assert sanitize_filename("Game  Name") == "Game Name"

    def test_clean_name_unchanged(self):
        assert sanitize_filename("Pokémon FireRed Version") == "Pokémon FireRed Version"


class TestRenameRoms:
    def _make_df(self, tmp_path: Path, rows: list[dict]) -> pd.DataFrame:
        """Build a DataFrame with the columns rename_roms expects."""
        return pd.DataFrame(rows)

    def test_matched_rom_is_renamed(self, tmp_path):
        rom = tmp_path / "game.gba"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Official Title", "matched": True},
        ])
        rename_roms(df)
        assert not rom.exists()
        assert (tmp_path / "Official Title.gba").exists()

    def test_unmatched_rom_is_not_renamed(self, tmp_path):
        rom = tmp_path / "game.gba"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Unknown/Unlinked", "matched": False},
        ])
        rename_roms(df)
        assert rom.exists()

    def test_already_correct_name_not_touched(self, tmp_path):
        rom = tmp_path / "Official Title.gba"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Official Title", "matched": True},
        ])
        rename_roms(df)
        assert rom.exists()

    def test_collision_skips_without_overwriting(self, tmp_path):
        old_rom = tmp_path / "old_name.gba"
        existing = tmp_path / "Official Title.gba"
        old_rom.write_bytes(b"OLD")
        existing.write_bytes(b"EXISTING")
        df = self._make_df(tmp_path, [
            {"path": str(old_rom), "ra_title": "Official Title", "matched": True},
        ])
        rename_roms(df)
        assert old_rom.exists()
        assert existing.read_bytes() == b"EXISTING"

    def test_title_with_colon_is_sanitized(self, tmp_path):
        rom = tmp_path / "game.gba"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Game: The Sequel", "matched": True},
        ])
        rename_roms(df)
        assert (tmp_path / "Game - The Sequel.gba").exists()

    def test_extension_is_preserved(self, tmp_path):
        rom = tmp_path / "game.iso"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Disc Game", "matched": True},
        ])
        rename_roms(df)
        assert (tmp_path / "Disc Game.iso").exists()

    def test_missing_file_on_disk_is_skipped(self, tmp_path):
        df = self._make_df(tmp_path, [
            {"path": str(tmp_path / "ghost.gba"), "ra_title": "Ghost Game", "matched": True},
        ])
        rename_roms(df)  # should not raise

    def test_empty_matched_df_does_not_raise(self, tmp_path):
        df = self._make_df(tmp_path, [
            {"path": str(tmp_path / "game.gba"), "ra_title": "Anything", "matched": False},
        ])
        rename_roms(df)  # no matched rows, should just print warning

    def test_dry_run_does_not_rename(self, tmp_path):
        rom = tmp_path / "game.gba"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Official Title", "matched": True},
        ])
        rename_roms(df, dry_run=True)
        assert rom.exists()
        assert not (tmp_path / "Official Title.gba").exists()

    def test_dry_run_reports_correct_count(self, tmp_path, capsys):
        rom = tmp_path / "game.gba"
        rom.write_bytes(b"DATA")
        df = self._make_df(tmp_path, [
            {"path": str(rom), "ra_title": "Official Title", "matched": True},
        ])
        rename_roms(df, dry_run=True)
        output = capsys.readouterr().out
        assert "Would rename" in output
