# ra-rom-manager

[![CI](https://github.com/lipofefeyt/ra-rom-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/lipofefeyt/ra-rom-manager/actions/workflows/ci.yml)

A personal ROM library manager built around [RetroAchievements](https://retroachievements.org). Scans your local ROM collection, verifies files against RA-accepted hashes, tracks achievement progress, and exports everything to a structured Excel workbook.

## Features

- Scans a local ROM library and computes MD5 hashes
- Matches ROMs against the official RetroAchievements hash database
- Supports multiple consoles in a single run (GBA, GB, GBC, SNES, NES, PS1, and more)
- Exports results to CSV (Excel coming in M4)
- Local caching to avoid redundant API calls (coming in M2)
- Achievement progress tracking per game (coming in M3)

## Prerequisites

- Python 3.12+
- A [RetroAchievements](https://retroachievements.org) account and API key
- ROMs organised in subfolders by console (e.g. `roms/gba/`, `roms/snes/`)

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/lipofefeyt/ra-rom-manager.git
cd ra-rom-manager

# 2. Install dependencies
pip install -e '.[dev]'

# 3. Configure your environment
cp .env.example .env
# Edit .env with your RA credentials and ROM path

# 4. Run
python main.py
```

Output is written to `data/identified_roms.csv`.

## ROM Folder Structure

The scanner infers the console from the subfolder name. Supported folder names:

| Folder | Console |
|--------|---------|
| `gba`  | Game Boy Advance |
| `gb`   | Game Boy |
| `gbc`  | Game Boy Color |
| `snes` | Super Nintendo |
| `nes`  | Nintendo Entertainment System |
| `psx` or `ps1` | PlayStation |
| `ps2`  | PlayStation 2 |
| `psp`  | PlayStation Portable |
| `md` or `genesis` | Mega Drive / Genesis |
| `sms`  | Master System |

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
RA_USERNAME=your_ra_username
RA_API_KEY=your_ra_api_key
ROM_PATH=/path/to/your/roms
```

## Project Structure

```
ra-rom-manager/
├── src/ra_manager/
│   ├── api_client.py   # RetroAchievements API wrapper
│   ├── cache.py        # Local cache layer (M2)
│   ├── config.py       # Console map, paths, settings
│   ├── matcher.py      # Hash matching logic
│   └── scanner.py      # ROM file walker and MD5 hasher
├── data/               # Output files and cache (gitignored)
├── tests/              # Unit tests
├── main.py             # Entry point
└── pyproject.toml
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)