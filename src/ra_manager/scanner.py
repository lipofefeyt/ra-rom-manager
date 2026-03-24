import hashlib
import os
import zipfile
from pathlib import Path

import pandas as pd

from .config import get_rom_path

# Extensions hashed directly
DIRECT_EXTENSIONS = {".gba", ".gb", ".gbc", ".sfc", ".smc", ".nes", ".iso", ".bin", ".chd"}

# Extensions that are zip archives containing a ROM
ZIP_EXTENSIONS = {".zip"}

# Extensions that are skipped entirely (with a logged reason)
SKIP_EXTENSIONS = {".cue"}  # .cue files are text descriptors — hash the paired .bin instead


class ROMScanner:
    def __init__(self, rom_dir=None):
        self.rom_dir = Path(rom_dir) if rom_dir else get_rom_path()

    def _hash_file(self, file_path: Path) -> str:
        """Hashes a file in 64 KB chunks. Returns lowercase hex MD5."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest().lower()

    def _hash_zip(self, file_path: Path) -> tuple[str | None, str | None]:
        """
        Extracts the first ROM file from a zip archive and hashes it in memory.
        Returns (md5, inner_filename) or (None, reason) if extraction fails.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                entries = [e for e in zf.namelist() if Path(e).suffix.lower() in DIRECT_EXTENSIONS]
                if not entries:
                    return None, "no supported ROM inside zip"

                inner_name = entries[0]
                hash_md5 = hashlib.md5()
                with zf.open(inner_name) as rom:
                    while chunk := rom.read(65536):
                        hash_md5.update(chunk)
                return hash_md5.hexdigest().lower(), inner_name

        except zipfile.BadZipFile:
            return None, "bad zip file"
        except Exception as e:
            return None, str(e)

    def scan(self) -> pd.DataFrame:
        """
        Walks the ROM directory and returns a DataFrame of all found ROMs.

        Columns:
            filename    — original file name on disk
            extension   — file extension
            path        — full path
            md5         — MD5 hash of the ROM content
            console     — inferred from parent folder name
            skipped     — True if the file was not hashed
            skip_reason — reason for skipping, empty string otherwise
        """
        print(f"📂 Scanning: {self.rom_dir}")
        rom_data = []

        for root, _dirs, files in os.walk(self.rom_dir):
            # Build a set of .bin files that have a paired .cue in this folder
            # so we don't double-hash them when they also appear as standalone .bin
            cue_files = {f for f in files if Path(f).suffix.lower() == ".cue"}
            cue_paired_bins = set()
            for cue in cue_files:
                cue_path = Path(root) / cue
                try:
                    bin_name = _parse_cue_bin(cue_path)
                    if bin_name:
                        cue_paired_bins.add(bin_name)
                except OSError:
                    pass

            for file in files:
                file_path = Path(root) / file
                suffix = file_path.suffix.lower()
                console = file_path.parent.name

                # Skip .cue descriptors — hash their paired .bin instead
                if suffix in SKIP_EXTENSIONS:
                    rom_data.append(
                        _skipped_row(
                            file,
                            suffix,
                            file_path,
                            console,
                            ".cue descriptor — paired .bin will be hashed",
                        )
                    )
                    continue

                if suffix in ZIP_EXTENSIONS:
                    print(f"  📦 Extracting: {file}")
                    md5, inner = self._hash_zip(file_path)
                    if md5 is None:
                        rom_data.append(_skipped_row(file, suffix, file_path, console, inner))
                    else:
                        rom_data.append(_rom_row(file, suffix, file_path, md5, console))
                    continue

                if suffix in DIRECT_EXTENSIONS:
                    print(f"  🔍 Hashing: {file}")
                    md5 = self._hash_file(file_path)
                    rom_data.append(_rom_row(file, suffix, file_path, md5, console))
                    continue

                # Anything else is silently ignored (e.g. .txt, .png, .srm saves)

        return pd.DataFrame(rom_data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_cue_bin(cue_path: Path) -> str | None:
    """
    Reads a .cue file and extracts the name of the first referenced .bin file.
    Returns None if none found.
    """
    with open(cue_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.upper().startswith("FILE"):
                # FILE "game.bin" BINARY  →  extract the quoted filename
                parts = line.split('"')
                if len(parts) >= 2:
                    return parts[1]
    return None


def _rom_row(filename: str, ext: str, path: Path, md5: str, console: str) -> dict:
    return {
        "filename": filename,
        "extension": ext,
        "path": str(path),
        "md5": md5,
        "console": console,
        "skipped": False,
        "skip_reason": "",
    }


def _skipped_row(filename: str, ext: str, path: Path, console: str, reason: str) -> dict:
    return {
        "filename": filename,
        "extension": ext,
        "path": str(path),
        "md5": "",
        "console": console,
        "skipped": True,
        "skip_reason": reason,
    }
