import hashlib
import os
import pandas as pd
from pathlib import Path
from .config import get_rom_path

class ROMScanner:
    def __init__(self, rom_dir=None):
        # If no dir is provided, use the one from config.py
        self.rom_dir = Path(rom_dir) if rom_dir else get_rom_path()
        self.supported_extensions = {'.bin', '.cue', '.chd', '.gba', '.sfc', '.zip', '.iso'}

    def calculate_md5(self, file_path):
        """Calculates MD5 in chunks to save memory (important for phone/large ISOs)."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # Read in 8KB chunks
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f"Error: {e}"

    def scan(self):
        """Walks through the ROM directory and builds a list of games."""
        print(f"Scanning directory: {self.rom_dir}")
        rom_data = []

        for root, dirs, files in os.walk(self.rom_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.supported_extensions:
                    print(f"Hashing: {file}...")
                    file_hash = self.calculate_md5(file_path)
                    
                    rom_data.append({
                        "filename": file,
                        "extension": file_path.suffix,
                        "path": str(file_path),
                        "md5": file_hash,
                        "console": file_path.parent.name # Assumes folders like 'psx', 'gba'
                    })
        
        # Turn the list into a Pandas DataFrame (your "Sheet")
        return pd.DataFrame(rom_data)

# Test the scanner
if __name__ == "__main__":
    scanner = ROMScanner()
    df = scanner.scan()
    print("\n--- Scan Results ---")
    print(df[['filename', 'md5']].head())
