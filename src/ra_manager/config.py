import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Console ID → name mapping as defined by RetroAchievements
# Full list: https://retroachievements.org/APIv1.php#get-consoleid
CONSOLES = {
    2:  "N64",
    3:  "SNES",
    4:  "GBA",
    5:  "GB",
    6:  "GBC",
    7:  "NES",
    11: "PlayStation",
    12: "PlayStation 2",
    13: "PC Engine",
    15: "Game Gear",
    18: "Nintendo DS",
    21: "PlayStation Portable",
    23: "Mega Drive",
    24: "Master System",
    39: "Saturn",
    56: "NeoGeo",
}

# Reverse map: folder name (lowercase) → console ID
# Scanner uses this to infer console from subfolder name
FOLDER_TO_CONSOLE_ID = {
    "n64": 2,
    "snes": 3,
    "gba": 4,
    "gb": 5,
    "gbc": 6,
    "nes": 7,
    "psx": 11,
    "ps1": 11,
    "ps2": 12,
    "pce": 13,
    "gg": 15,
    "nds": 18,
    "sms": 24,
    "psp": 21,
    "md": 23,
    "genesis": 23,
    "saturn": 39,
    "neogeo": 56
}


def get_rom_path() -> Path:
    raw = os.getenv("ROM_PATH")
    if not raw:
        raise OSError("ROM_PATH is not set in your .env file.")
    path = Path(raw)
    if not path.exists():
        raise FileNotFoundError(f"ROM_PATH does not exist: {path}")
    return path
