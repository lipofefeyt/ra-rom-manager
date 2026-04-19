import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Console ID → name mapping as defined by RetroAchievements
# Full list: https://retroachievements.org/APIv1.php#get-consoleid
CONSOLES = {
    2: "N64",
    3: "SNES",
    4: "GB",
    5: "GBA",
    6: "GBC",
    7: "NES",
    12: "PlayStation",
    21: "PlayStation 2",
    13: "PC Engine",
    15: "Game Gear",
    16: "GameCube",
    18: "Nintendo DS",
    41: "PlayStation Portable",
    23: "Mega Drive",
    24: "Master System",
    39: "Saturn",
    56: "NeoGeo",
}

# Reverse map: folder name (lowercase) → console ID
# Scanner uses this to infer console from subfolder name
FOLDER_TO_CONSOLE_ID = {
    "n64": 2,  # Nintendo 64
    "snes": 3,  # Nintendo SNES1
    "gb": 4,  # Nintendo Game Boy
    "gba": 5,  # Nintendo Game Boy Advance
    "gbc": 6,  # Nintendo Game Boy Color
    "nes": 7,  # Nintendo NES
    "psx": 12,  # Sony Playstation 1
    "ps1": 12,  # Sony Playstation 1
    "ps2": 21,  # Sony Playstation 2
    "pce": 13,  # NEC PC Engine
    "gg": 15,  # SEGA Game Gear
    "gamecube": 16,  # Nintendo Game Cube
    "gc": 16,  # Nintendo Game Cube
    "nds": 18,  # Nintendo DS
    "psp": 41,  # Sony Playstation Portable
    "md": 23,  # SEGA Mega Drive
    "genesis": 23,  # SEGA Genesis
    "sms": 24,  # SEGA Master System
    "saturn": 39,  # SEGA Saturn
    "neogeo": 56,  # SNK NeoGeo
}


def get_rom_path() -> Path:
    raw = os.getenv("ROM_PATH")
    if not raw:
        raise OSError("ROM_PATH is not set in your .env file.")
    path = Path(raw)
    if not path.exists():
        raise FileNotFoundError(f"ROM_PATH does not exist: {path}")
    return path
