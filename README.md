# ra-rom-manager

[![CI](https://github.com/lipofefeyt/ra-rom-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/lipofefeyt/ra-rom-manager/actions/workflows/ci.yml)

> **Author:** lipofefeyt
> **Version:** 1.1.0
> **Status:** Active — M1–M4 complete, M5 in progress

A personal ROM library manager built around [RetroAchievements](https://retroachievements.org). Scans your local ROM collection, verifies files against RA-accepted hashes, tracks achievement progress per game, and exports everything to a structured Excel workbook.

---

## Features

- Scans a local ROM library and computes MD5 hashes
- Matches ROMs against the official RetroAchievements hash database
- Supports multiple consoles in a single run (GBA, GB, GBC, SNES, NES, PS1, PS2, N64, NDS, Saturn, NeoGeo, Mega Drive, and more)
- TTL-based local cache — fast after first run, no redundant API calls
- Handles `.zip` archives (extracts and hashes in memory) and `.cue`/`.bin` pairs correctly
- Fetches achievement progress per matched game (earned, total, completion %, mastered)
- Exports to `data/ra_collection.xlsx` with per-console sheets, a Summary sheet, and a Want to Play sheet
- Conditional formatting: 🟢 mastered, 🟡 in progress, 🔴 unmatched
- *(M5)* Suggests the correct RA-accepted dump filename for unmatched ROMs

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

# 4. Run
python main.py
```

Output is written to `data/ra_collection.xlsx`.

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
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── ci.yml
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
│       ├── matcher.py           # Hash matching logic
│       ├── scanner.py           # ROM file walker and MD5 hasher
│       └── stats.py             # Achievement progress enrichment
├── tests/
│   └── fixtures/
│       └── mock_ra_data.json
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
| M5 — ROM Sourcing Hints | 🔜 In Progress | Suggest correct dump for unmatched ROMs |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Requirements

See [REQUIREMENTS.md](REQUIREMENTS.md).

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

[MIT](LICENSE) — lipofefeyt