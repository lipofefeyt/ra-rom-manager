import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path


def _xdelta3_available() -> bool:
    return shutil.which("xdelta3") is not None


def _download(url: str, dest: Path) -> None:
    urllib.request.urlretrieve(url, dest)


def apply_patches(df, dry_run: bool = False) -> None:
    """
    For each unmatched ROM that has a patch_url, download and apply the patch
    using xdelta3. Writes patched file alongside original with a _patched suffix.
    Original files are never overwritten.
    """
    if not _xdelta3_available():
        print(
            "⚠️  xdelta3 not found. Install it and re-run with --patch.\n"
            "    Ubuntu/Debian: sudo apt install xdelta3\n"
            "    macOS:         brew install xdelta"
        )
        return

    candidates = df[
        (~df["matched"]) & df["patch_url"].notna() & (df["patch_url"] != "")
    ]

    if candidates.empty:
        print("   No unmatched ROMs with a patch URL found.")
        return

    patched = skipped = failed = 0

    for _, row in candidates.iterrows():
        rom_path = Path(row["path"])
        patch_url = row["patch_url"]
        stem = rom_path.stem
        suffix = rom_path.suffix
        out_path = rom_path.with_name(f"{stem}_patched{suffix}")

        if out_path.exists():
            print(f"   ⏭️  Already patched, skipping: {out_path.name}")
            skipped += 1
            continue

        if dry_run:
            print(f"   [dry-run] Would patch: {rom_path.name} → {out_path.name}")
            patched += 1
            continue

        if not rom_path.exists():
            print(f"   ⚠️  Source file missing, skipping: {rom_path}")
            skipped += 1
            continue

        print(f"   ⬇️  Downloading patch for {rom_path.name}...")
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".xdelta", delete=False
            ) as tmp:
                patch_file = Path(tmp.name)
            _download(patch_url, patch_file)

            result = subprocess.run(
                ["xdelta3", "-d", "-s", str(rom_path), str(patch_file), str(out_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"   ✅ Patched: {out_path.name}")
                patched += 1
            else:
                print(f"   ❌ xdelta3 failed for {rom_path.name}: {result.stderr.strip()}")
                failed += 1
                if out_path.exists():
                    out_path.unlink()
        except Exception as e:
            print(f"   ❌ Error patching {rom_path.name}: {e}")
            failed += 1
        finally:
            if patch_file.exists():
                patch_file.unlink()

    label = "Would patch" if dry_run else "Patched"
    print(f"\n   {label}: {patched}  |  Skipped: {skipped}  |  Failed: {failed}")
