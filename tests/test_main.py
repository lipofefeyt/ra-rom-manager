from unittest.mock import MagicMock, patch

import pandas as pd

import main as main_module


def _make_scan_df():
    return pd.DataFrame({
        "filename": ["rayman.gba"],
        "md5": ["fb20d6009c7400f37581f81ae5b1e917"],
        "console": ["gba"],
        "skipped": [False],
        "skip_reason": [None],
        "extension": [".gba"],
        "path": ["/roms/gba/rayman.gba"],
    })


def _make_enriched_df():
    df = _make_scan_df().copy()
    df["ra_title"] = ["Rayman Advance"]
    df["ra_game_id"] = [1141]
    df["matched"] = [True]
    df["suggested_title"] = [None]
    df["suggested_filename"] = [None]
    df["suggested_md5"] = [None]
    df["patch_url"] = [None]
    df["earned"] = [15]
    df["total"] = [50]
    df["completion_pct"] = [30.0]
    df["is_mastered"] = [False]
    df["status"] = ["In Progress (30.0%)"]
    return df


class TestConsoleFlag:
    def test_unknown_console_prints_error_and_returns(self, capsys):
        with patch("main.RAClient"), \
             patch("main.ROMScanner") as MockScanner, \
             patch("main.argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                console="doesnotexist", hint=False, refresh=False,
                franchise=None, rename=False, dry_run=False,
                exclude=[], timestamp=False, csv=False, html=False,
                serve=False, patch=False,
            )
            MockScanner.return_value.scan.return_value = _make_scan_df()
            main_module.main()

        out = capsys.readouterr().out
        assert "Unknown console" in out
        assert "doesnotexist" in out

    def test_known_console_filters_detected_consoles(self):
        enriched = _make_enriched_df()

        with patch("main.RAClient"), \
             patch("main.ROMScanner") as MockScanner, \
             patch("main.HashMatcher") as MockMatcher, \
             patch("main.enrich_with_progress", return_value=enriched), \
             patch("main.export"), \
             patch("main.argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                console="gba", hint=False, refresh=False,
                franchise=None, rename=False, dry_run=False,
                exclude=[], timestamp=False, csv=False, html=False,
                serve=False, patch=False,
            )
            MockScanner.return_value.scan.return_value = _make_scan_df()
            mock_matcher = MagicMock()
            mock_matcher.match.return_value = enriched
            mock_matcher.enrich_with_dump_hints.return_value = enriched
            MockMatcher.return_value = mock_matcher

            main_module.main()

        # Only the gba console should have been processed — matcher called once
        assert mock_matcher.match.call_count == 1


class TestHintFlag:
    def test_hint_mode_skips_enrich_with_progress(self):
        enriched = _make_enriched_df()

        with patch("main.RAClient"), \
             patch("main.ROMScanner") as MockScanner, \
             patch("main.HashMatcher") as MockMatcher, \
             patch("main.enrich_with_progress") as mock_enrich, \
             patch("main.export"), \
             patch("main.argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                console=None, hint=True, refresh=False,
                franchise=None, rename=False, dry_run=False,
                exclude=[], timestamp=False, csv=False, html=False,
                serve=False, patch=False,
            )
            MockScanner.return_value.scan.return_value = _make_scan_df()
            mock_matcher = MagicMock()
            mock_matcher.match.return_value = enriched
            mock_matcher.enrich_with_dump_hints.return_value = enriched
            MockMatcher.return_value = mock_matcher

            main_module.main()

        mock_enrich.assert_not_called()

    def test_hint_mode_still_exports(self):
        enriched = _make_enriched_df()

        with patch("main.RAClient"), \
             patch("main.ROMScanner") as MockScanner, \
             patch("main.HashMatcher") as MockMatcher, \
             patch("main.enrich_with_progress"), \
             patch("main.export") as mock_export, \
             patch("main.argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                console=None, hint=True, refresh=False,
                franchise=None, rename=False, dry_run=False,
                exclude=[], timestamp=False, csv=False, html=False,
                serve=False, patch=False,
            )
            MockScanner.return_value.scan.return_value = _make_scan_df()
            mock_matcher = MagicMock()
            mock_matcher.match.return_value = enriched
            mock_matcher.enrich_with_dump_hints.return_value = enriched
            MockMatcher.return_value = mock_matcher

            main_module.main()

        mock_export.assert_called_once()
