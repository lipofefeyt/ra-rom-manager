from unittest.mock import MagicMock, patch

import pandas as pd

from src.ra_manager.patcher import apply_patches


def _make_df(rows):
    return pd.DataFrame(
        rows,
        columns=["filename", "path", "matched", "patch_url"],
    )


class TestApplyPatches:
    def test_prints_install_hint_when_xdelta3_missing(self, capsys):
        with patch("src.ra_manager.patcher._xdelta3_available", return_value=False):
            apply_patches(_make_df([]))
        assert "xdelta3 not found" in capsys.readouterr().out

    def test_no_candidates_prints_message(self, capsys):
        df = _make_df([("rayman.gba", "/roms/rayman.gba", True, None)])
        with patch("src.ra_manager.patcher._xdelta3_available", return_value=True):
            apply_patches(df)
        assert "No unmatched ROMs" in capsys.readouterr().out

    def test_dry_run_does_not_call_subprocess(self, tmp_path, capsys):
        rom = tmp_path / "unknown.gba"
        rom.write_bytes(b"\x00" * 16)
        df = _make_df([("unknown.gba", str(rom), False, "https://example.com/patch.xdelta")])

        with patch("src.ra_manager.patcher._xdelta3_available", return_value=True), \
             patch("src.ra_manager.patcher.subprocess.run") as mock_run:
            apply_patches(df, dry_run=True)

        mock_run.assert_not_called()
        assert "dry-run" in capsys.readouterr().out

    def test_skips_already_patched_file(self, tmp_path, capsys):
        rom = tmp_path / "unknown.gba"
        rom.write_bytes(b"\x00" * 16)
        already = tmp_path / "unknown_patched.gba"
        already.write_bytes(b"\x00" * 16)
        df = _make_df([("unknown.gba", str(rom), False, "https://example.com/patch.xdelta")])

        with patch("src.ra_manager.patcher._xdelta3_available", return_value=True):
            apply_patches(df)

        assert "Already patched" in capsys.readouterr().out

    def test_successful_patch_calls_xdelta3(self, tmp_path, capsys):
        rom = tmp_path / "unknown.gba"
        rom.write_bytes(b"\x00" * 16)
        df = _make_df([("unknown.gba", str(rom), False, "https://example.com/patch.xdelta")])

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("src.ra_manager.patcher._xdelta3_available", return_value=True), \
             patch("src.ra_manager.patcher._download"), \
             patch("src.ra_manager.patcher.subprocess.run", return_value=mock_result):
            apply_patches(df)

        assert "Patched" in capsys.readouterr().out

    def test_failed_xdelta3_reports_error(self, tmp_path, capsys):
        rom = tmp_path / "unknown.gba"
        rom.write_bytes(b"\x00" * 16)
        df = _make_df([("unknown.gba", str(rom), False, "https://example.com/patch.xdelta")])

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "bad delta"

        with patch("src.ra_manager.patcher._xdelta3_available", return_value=True), \
             patch("src.ra_manager.patcher._download"), \
             patch("src.ra_manager.patcher.subprocess.run", return_value=mock_result):
            apply_patches(df)

        assert "failed" in capsys.readouterr().out.lower()
