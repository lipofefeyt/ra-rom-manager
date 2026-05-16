import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from src.ra_manager.scanner import ROMScanner


@pytest.fixture
def rom_dir(tmp_path):
    """A minimal ROM directory with a gba/ subfolder."""
    gba = tmp_path / "gba"
    gba.mkdir()
    return tmp_path


def _write_rom(path: Path, content: bytes = b"FAKEROM") -> Path:
    path.write_bytes(content)
    return path


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


class TestScanBasic:
    def test_finds_gba_rom(self, rom_dir):
        _write_rom(rom_dir / "gba" / "game.gba")
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert "game.gba" in df["filename"].values

    def test_correct_console_inferred_from_folder(self, rom_dir):
        _write_rom(rom_dir / "gba" / "game.gba")
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert df.loc[df["filename"] == "game.gba", "console"].iloc[0] == "gba"

    def test_md5_is_correct(self, rom_dir):
        content = b"TESTROM_CONTENT"
        _write_rom(rom_dir / "gba" / "game.gba", content)
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert df.loc[df["filename"] == "game.gba", "md5"].iloc[0] == _md5(content)

    def test_multiple_consoles_in_one_scan(self, tmp_path):
        (tmp_path / "gba").mkdir()
        (tmp_path / "snes").mkdir()
        _write_rom(tmp_path / "gba" / "a.gba")
        _write_rom(tmp_path / "snes" / "b.sfc")
        df = ROMScanner(rom_dir=tmp_path).scan()
        assert set(df["console"].unique()) == {"gba", "snes"}

    def test_empty_rom_dir_returns_empty_dataframe(self, tmp_path):
        df = ROMScanner(rom_dir=tmp_path).scan()
        assert df.empty

    def test_unknown_extension_not_included(self, rom_dir):
        _write_rom(rom_dir / "gba" / "readme.txt")
        df = ROMScanner(rom_dir=rom_dir).scan()
        # No supported extensions → empty DataFrame
        assert df.empty

    def test_skipped_column_false_for_valid_rom(self, rom_dir):
        _write_rom(rom_dir / "gba" / "game.gba")
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert not df.loc[df["filename"] == "game.gba", "skipped"].iloc[0]


class TestZipHandling:
    def _make_zip(self, zip_path: Path, inner_name: str, content: bytes) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(inner_name, content)
        zip_path.write_bytes(buf.getvalue())

    def test_zip_rom_is_hashed(self, rom_dir):
        content = b"INNER_ROM_CONTENT"
        self._make_zip(rom_dir / "gba" / "game.zip", "game.gba", content)
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert df.loc[df["filename"] == "game.zip", "md5"].iloc[0] == _md5(content)

    def test_zip_not_skipped(self, rom_dir):
        self._make_zip(rom_dir / "gba" / "game.zip", "game.gba", b"DATA")
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert not df.loc[df["filename"] == "game.zip", "skipped"].iloc[0]

    def test_zip_with_no_rom_inside_is_skipped(self, rom_dir):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("readme.txt", "no rom here")
        (rom_dir / "gba" / "empty.zip").write_bytes(buf.getvalue())
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert df.loc[df["filename"] == "empty.zip", "skipped"].iloc[0]

    def test_bad_zip_is_skipped(self, rom_dir):
        (rom_dir / "gba" / "corrupt.zip").write_bytes(b"not a zip")
        df = ROMScanner(rom_dir=rom_dir).scan()
        assert df.loc[df["filename"] == "corrupt.zip", "skipped"].iloc[0]


class TestCueBinHandling:
    def test_cue_file_is_skipped(self, tmp_path):
        psx = tmp_path / "psx"
        psx.mkdir()
        bin_path = psx / "game.bin"
        bin_path.write_bytes(b"DISC_DATA")
        cue = psx / "game.cue"
        cue.write_text('FILE "game.bin" BINARY\n  TRACK 01 MODE1/2352\n')
        df = ROMScanner(rom_dir=tmp_path).scan()
        cue_row = df[df["filename"] == "game.cue"]
        assert cue_row.iloc[0]["skipped"]

    def test_bin_paired_with_cue_is_hashed(self, tmp_path):
        psx = tmp_path / "psx"
        psx.mkdir()
        content = b"DISC_DATA"
        bin_path = psx / "game.bin"
        bin_path.write_bytes(content)
        cue = psx / "game.cue"
        cue.write_text('FILE "game.bin" BINARY\n  TRACK 01 MODE1/2352\n')
        df = ROMScanner(rom_dir=tmp_path).scan()
        bin_row = df[df["filename"] == "game.bin"]
        assert not bin_row.empty
        assert bin_row.iloc[0]["md5"] == _md5(content)


class TestExcludeDirs:
    def test_excluded_folder_is_not_scanned(self, tmp_path):
        gba = tmp_path / "gba"
        gba.mkdir()
        _write_rom(gba / "game.gba")
        df = ROMScanner(rom_dir=tmp_path, exclude_dirs=["gba"]).scan()
        # Only folder is excluded → nothing scanned
        assert df.empty

    def test_non_excluded_folder_is_scanned(self, tmp_path):
        gba = tmp_path / "gba"
        snes = tmp_path / "snes"
        gba.mkdir()
        snes.mkdir()
        _write_rom(gba / "a.gba")
        _write_rom(snes / "b.sfc")
        df = ROMScanner(rom_dir=tmp_path, exclude_dirs=["gba"]).scan()
        assert "b.sfc" in df["filename"].values
        assert "a.gba" not in df["filename"].values

    def test_exclude_is_case_insensitive(self, tmp_path):
        gba = tmp_path / "gba"
        gba.mkdir()
        _write_rom(gba / "game.gba")
        df = ROMScanner(rom_dir=tmp_path, exclude_dirs=["GBA"]).scan()
        assert df.empty
