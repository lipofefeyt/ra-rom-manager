# ra-rom-manager

[![CI](https://github.com/lipofefeyt/ra-rom-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/lipofefeyt/ra-rom-manager/actions/workflows/ci.yml)

> **Author:** lipofefeyt
> **Version:** 1.2.0
> **Status:** Active — M1–M5.5 complete

A personal ROM library manager built around [RetroAchievements](https://retroachievements.org). Scans your local ROM collection, verifies files against RA-accepted hashes, tracks achievement progress per game, exports everything to a structured Excel workbook, and safely auto-renames your valid files.

---

## Features

- Scans a local ROM library and computes MD5 hashes
- Matches ROMs against the official RetroAchievements hash database
- Supports multiple consoles in a single run (GBA, GB, GBC, SNES, NES, PS1, PS2, PSP, GameCube, N64, NDS, Saturn, NeoGeo, Mega Drive, and more)
- TTL-based local cache — fast after first run, no redundant API calls
- Handles `.zip` archives (extracts and hashes in memory) and `.cue`/`.bin` pairs correctly
- Fetches achievement progress per matched game (earned, total, completion %, mastered)
- Exports to `data/ra_collection.xlsx` with per-console sheets, a Summary sheet, and a Want to Play sheet
- Conditional formatting: 🟢 mastered, 🟡 in progress, 🔴 unmatched
- Suggests the exact RA-accepted dump filename and patch URL for unmatched ROMs
- **(New in M5.5)** Safely auto-renames perfectly matched ROMs to official RA titles via the `--rename` flag

---

## Prerequisites

- Python 3.12+
- A [RetroAchievements](https://retroachievements.org) account and API key
- ROMs organised in subfolders by console (e.g. `roms/gba/`, `roms/snes/`)

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/lipofefeyt/ra-rom-manager.git
cd ra-rom-manager

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure your environment
cp .env.example .env
# Edit .env with your RA credentials and ROM path

# 4. Run (Standard Report)
python main.py

# 5. Run (With Auto-Renamer)
python main.py --rename
```

Output is written to `data/ra_collection.xlsx`.

---

## How It Works (Under the Hood)

For those wanting to understand how the manager processes data:
1. **Scanner**: Walks your ROM folder, identifies the console via the subfolder name, and hashes the file into an MD5 string. It skips descriptors (like `.cue`) and extracts `.zip` contents in memory automatically.
2. **Matcher & API**: Compares your local hashes with RetroAchievements' database. Everything is aggressively cached locally (`data/cache.json`) so your API limits stay safe.
3. **Stats**: If a ROM matches, it fetches your personal account's achievement progress for that game.
4. **Sourcing Hints**: If a ROM *doesn't* match, the system uses deep string normalization and fuzzy-matching on your filename to guess what game you *meant* to add, and calls RA to tell you the exact No-Intro/Redump filename you should download instead.
5. **Auto-Renamer**: If requested via the `--rename` flag, safely cleans up your library by renaming your mathematically matched ROMs to their official titles.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
RA_USERNAME=your_ra_username
RA_API_KEY=your_ra_api_key
ROM_PATH=/path/to/your/roms
```

---

## ROM Folder Structure

The scanner infers the console from the subfolder name. Supported folder names:

| Folder | Console |
|--------|---------|
| `gba` | Game Boy Advance |
| `gb` | Game Boy |
| `gbc` | Game Boy Color |
| `snes` | Super Nintendo |
| `nes` | NES |
| `psx` / `ps1` | PlayStation |
| `ps2` | PlayStation 2 |
| `psp` | PlayStation Portable |
| `gc` / `gamecube` | Nintendo GameCube |
| `n64` | Nintendo 64 |
| `nds` | Nintendo DS |
| `md` / `genesis` | Mega Drive / Genesis |
| `sms` | Master System |
| `saturn` | Saturn |
| `neogeo` | NeoGeo |

Unknown folder names are logged as warnings and skipped.

---

## Project Structure

```
ra-rom-manager/
├── .devcontainer/
├── .github/
├── data/                        # gitignored — runtime outputs
│   ├── cache.json
│   ├── ra_collection.xlsx
│   └── want_to_play.csv
├── docs/
│   └── ARCHITECTURE.md
├── src/
│   └── ra_manager/
│       ├── api_client.py        # RetroAchievements API wrapper
│       ├── cache.py             # TTL-based local JSON cache
│       ├── config.py            # Console map, paths, settings
│       ├── exporter.py          # Excel workbook export
│       ├── matcher.py           # Hash matching logic & normalizer
│       ├── renamer.py           # Strict hash-based file auto-renamer
│       ├── scanner.py           # ROM file walker and MD5 hasher
│       └── stats.py             # Achievement progress enrichment
├── tests/
├── tutorial/
│   └── ADDING_A_NEW_CONSOLE.md
├── main.py
├── pyproject.toml
├── REQUIREMENTS.md
└── issues.json
```

---

## Milestones

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1 — Clean Foundation | ✅ Complete | Devcontainer, CI, pyproject.toml, core refactor |
| M2 — Multi-Console & Caching | ✅ Complete | Cache layer, scanner fixes, multi-console |
| M3 — Achievement Tracking | ✅ Complete | Progress fetching, stats enrichment |
| M4 — Excel Output & Stats | ✅ Complete | Full Excel export with formatting |
| M5 — ROM Sourcing Hints | ✅ Complete | Suggest correct dump for unmatched ROMs |
| M5.5 — File Management | ✅ Complete | Safe, strict hash-based auto-renaming tool |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Requirements

See [REQUIREMENTS.md](REQUIREMENTS.md).

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

[MIT](LICENSE) — lipofefeyt