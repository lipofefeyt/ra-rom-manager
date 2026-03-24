import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Console ID → name mapping as defined by RetroAchievements
# Full list: https://retroachievements.org/APIv1.php#get-consoleid
CONSOLES = {
    3:  "SNES",
    4:  "GBA",
    5:  "GB",
    6:  "GBC",
    7:  "NES",
    11: "PlayStation",
    12: "PlayStation 2",
    13: "PC Engine",
    15: "Game Gear",
    17: "Jaguar",
    18: "Saturn",
    21: "PlayStation Portable",
    23: "Mega Drive",
    24: "Master System",
    25: "Atari Lynx",
}

# Reverse map: folder name (lowercase) → console ID
# Scanner uses this to infer console from subfolder name
FOLDER_TO_CONSOLE_ID = {
    "snes":  3,
    "gba":   4,
    "gb":    5,
    "gbc":   6,
    "nes":   7,
    "psx":   11,
    "ps1":   11,
    "ps2":   12,
    "pce":   13,
    "gg":    15,
    "sms":   24,
    "psp":   21,
    "md":    23,
    "genesis": 23,
}


def get_rom_path() -> Path:
    raw = os.getenv("ROM_PATH")
    if not raw:
        raise EnvironmentError("ROM_PATH is not set in your .env file.")
    path = Path(raw)
    if not path.exists():
        raise FileNotFoundError(f"ROM_PATH does not exist: {path}")
    return path