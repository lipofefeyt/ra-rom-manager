# RA ROM Manager — Development Requirements

> **Status:** Active — v1.1
> **Last updated:** 2026-03
> **Author:** lipofefeyt

---

## Overview

This document defines the development requirements for the RA ROM Manager tool. Requirements describe what the tool must do and how it must behave. They are distinct from any specific implementation detail.

Requirements are identified by the prefix `RA-DEV-` followed by a zero-padded sequence number. Each requirement belongs to a functional area, indicated by the area tag in square brackets.

### Functional Areas

| Tag | Area |
| --- | --- |
| [SCAN] | ROM Scanning & Hashing |
| [MATCH] | Hash Matching & Identification |
| [API] | RetroAchievements API Client |
| [CACHE] | Local Caching Layer |
| [STATS] | Achievement Progress & Statistics |
| [OUT] | Output & Export |
| [SYS] | System & Infrastructure |

### Requirement Status Values

| Status | Meaning |
| --- | --- |
| DRAFT | Under discussion, not yet baselined |
| BASELINED | Agreed and frozen for current milestone |
| IMPLEMENTED | Closed by a committed and merged implementation |
| DEFERRED | Out of scope for current milestone, retained for future |
| SUPERSEDED | Replaced by a later requirement |

---

## ROM Scanning & Hashing Requirements [SCAN]

**RA-DEV-001** `[SCAN]` `IMPLEMENTED`
The scanner shall walk a configurable root ROM directory recursively and compute the MD5 hash of every supported ROM file.

**RA-DEV-002** `[SCAN]` `IMPLEMENTED`
The scanner shall use 64 KB read chunks when hashing files to ensure acceptable performance on large ISOs and disc images.

**RA-DEV-003** `[SCAN]` `IMPLEMENTED`
The scanner shall infer the console for each ROM from the name of its immediate parent folder, using the `FOLDER_TO_CONSOLE_ID` map defined in `config.py`.

**RA-DEV-004** `[SCAN]` `IMPLEMENTED`
The scanner shall handle `.zip` archives by extracting the first supported ROM file in memory and hashing its contents, without writing any temporary files to disk.

**RA-DEV-005** `[SCAN]` `IMPLEMENTED`
The scanner shall skip `.cue` descriptor files and instead hash the `.bin` file they reference.

**RA-DEV-006** `[SCAN]` `IMPLEMENTED`
The scanner shall produce a DataFrame with columns: `filename`, `extension`, `path`, `md5`, `console`, `skipped`, `skip_reason`.

**RA-DEV-007** `[SCAN]` `IMPLEMENTED`
The scanner shall log a warning for unknown console folder names and skip them without aborting the run.

---

## Hash Matching & Identification Requirements [MATCH]

**RA-DEV-010** `[MATCH]` `IMPLEMENTED`
The matcher shall build a flat `{md5: (title, game_id)}` lookup map from the RA game list, normalising all hashes to lowercase.

**RA-DEV-011** `[MATCH]` `IMPLEMENTED`
The matcher shall add `ra_title`, `ra_game_id`, and `matched` columns to the scanned ROM DataFrame.

**RA-DEV-012** `[MATCH]` `IMPLEMENTED`
The matcher shall not mutate the input DataFrame — it shall always operate on a copy.

**RA-DEV-013** `[MATCH]` `BASELINED`
For unmatched ROMs, the matcher shall suggest the closest RA-accepted dump by fuzzy title match, adding `suggested_title`, `suggested_md5`, `suggested_filename`, and `patch_url` columns. Assigned to M5.

**RA-DEV-014** `[MATCH]` `BASELINED`
The suggested filename shall be sourced from the `API_GetGameHashes` endpoint `Name` field, which contains the exact No-Intro filename RA expects. Assigned to M5.

---

## RetroAchievements API Client Requirements [API]

**RA-DEV-020** `[API]` `IMPLEMENTED`
The API client shall authenticate all requests using `RA_USERNAME` and `RA_API_KEY` sourced from `.env`.

**RA-DEV-021** `[API]` `IMPLEMENTED`
The API client shall apply a 10-second timeout to all HTTP requests.

**RA-DEV-022** `[API]` `IMPLEMENTED`
The API client shall raise `RAClientError` for all network-level failures, HTTP errors, and timeouts. It shall never swallow exceptions silently.

**RA-DEV-023** `[API]` `IMPLEMENTED`
The API client shall expose `get_console_game_hashes(console_id)` returning the full game and hash list for a console.

**RA-DEV-024** `[API]` `IMPLEMENTED`
The API client shall expose `get_user_progress(game_id)` returning `{earned, total, points_earned, points_total, is_mastered}` for the configured user on a given game.

**RA-DEV-025** `[API]` `IMPLEMENTED`
The API client shall expose `get_user_summary()` returning `{points, softcore_points, rank, games_played}` for the configured user.

**RA-DEV-026** `[API]` `BASELINED`
The API client shall expose `get_game_hashes(game_id)` returning `[{MD5, Name, Labels, PatchUrl}]` for a given game, sourced from `API_GetGameHashes`. Assigned to M5.

---

## Local Caching Layer Requirements [CACHE]

**RA-DEV-030** `[CACHE]` `IMPLEMENTED`
All API responses shall be cached locally in `data/cache.json` to avoid redundant network calls.

**RA-DEV-031** `[CACHE]` `IMPLEMENTED`
Hash list responses shall be cached with a 24-hour TTL. Progress and summary responses shall be cached with a 1-hour TTL.

**RA-DEV-032** `[CACHE]` `IMPLEMENTED`
All `RAClient` methods shall accept a `force_refresh=True` parameter to bypass the cache and update it with fresh data.

**RA-DEV-033** `[CACHE]` `IMPLEMENTED`
The cache shall be resilient to corruption — a malformed `cache.json` shall return `None` for all keys without raising an exception.

**RA-DEV-034** `[CACHE]` `IMPLEMENTED`
`cache.clear_all()` shall wipe the entire cache file.

---

## Achievement Progress & Statistics Requirements [STATS]

**RA-DEV-040** `[STATS]` `IMPLEMENTED`
The stats layer shall enrich the matched DataFrame with `earned`, `total`, `completion_pct`, `is_mastered`, and `status` columns by calling `get_user_progress()` for each matched ROM.

**RA-DEV-041** `[STATS]` `IMPLEMENTED`
Unmatched ROMs shall receive a `status` of `"Unmatched"` without triggering any API call.

**RA-DEV-042** `[STATS]` `IMPLEMENTED`
`get_completion_label()` shall return human-readable status strings: `"Unplayed"`, `"In Progress (X%)"`, `"Mastered 🏆"`, or `"No Achievements"`.

**RA-DEV-043** `[STATS]` `IMPLEMENTED`
A per-game API error shall set `status` to `"Error"` and log a warning, without aborting the enrichment of other games.

---

## Output & Export Requirements [OUT]

**RA-DEV-050** `[OUT]` `IMPLEMENTED`
The exporter shall produce a multi-sheet Excel workbook at `data/ra_collection.xlsx`.

**RA-DEV-051** `[OUT]` `IMPLEMENTED`
The workbook shall contain a Summary sheet (always first) with user profile stats and collection overview.

**RA-DEV-052** `[OUT]` `IMPLEMENTED`
The workbook shall contain one sheet per detected console, with conditional row formatting: green for mastered, yellow for in-progress, red for unmatched.

**RA-DEV-053** `[OUT]` `IMPLEMENTED`
The workbook shall contain a Want to Play sheet (always last), populated from `data/want_to_play.csv` if present.

**RA-DEV-054** `[OUT]` `BASELINED`
The workbook shall contain an Unmatched ROMs sheet listing all unmatched ROMs alongside their suggested correct dump filename, MD5, and patch URL where available. Assigned to M5.

**RA-DEV-055** `[OUT]` `DEFERRED`
The exporter shall support an optional HTML report output in addition to the Excel workbook.

---

## System & Infrastructure Requirements [SYS]

**RA-DEV-060** `[SYS]` `IMPLEMENTED`
The tool shall be packaged as a pip-installable Python package using `pyproject.toml` with separate `dev` dependencies.

**RA-DEV-061** `[SYS]` `IMPLEMENTED`
The tool shall support Python 3.12 and above.

**RA-DEV-062** `[SYS]` `IMPLEMENTED`
The tool shall support Windows 10 and above as the primary execution environment, given the target user's ROM library is stored on a Windows-accessible drive.

**RA-DEV-063** `[SYS]` `IMPLEMENTED`
The tool shall be executable inside a GitHub Codespace via a `.devcontainer` configuration with zero manual setup.

**RA-DEV-064** `[SYS]` `IMPLEMENTED`
A CI pipeline shall run on every push and PR to `main`, executing Ruff linting and the full pytest suite.

**RA-DEV-065** `[SYS]` `IMPLEMENTED`
All configuration (API credentials, ROM path) shall be sourced from a `.env` file and never hardcoded or committed.

**RA-DEV-066** `[SYS]` `IMPLEMENTED`
The codebase shall maintain zero Ruff violations on every CI run.

---

## Traceability Index

| Requirement ID | Area | Status | Milestone | Verified By |
| --- | --- | --- | --- | --- |
| RA-DEV-001 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-002 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-003 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-004 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-005 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-006 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-007 | SCAN | IMPLEMENTED | M2 | test_scanner (manual) |
| RA-DEV-010 | MATCH | IMPLEMENTED | M1 | test_matcher.py |
| RA-DEV-011 | MATCH | IMPLEMENTED | M1 | test_matcher.py |
| RA-DEV-012 | MATCH | IMPLEMENTED | M1 | TestMatch::test_original_df_not_mutated |
| RA-DEV-013 | MATCH | BASELINED | M5 | — |
| RA-DEV-014 | MATCH | BASELINED | M5 | — |
| RA-DEV-020 | API | IMPLEMENTED | M1 | test_api_client.py |
| RA-DEV-021 | API | IMPLEMENTED | M2 | TestGetConsoleGameHashes::test_raises_on_timeout |
| RA-DEV-022 | API | IMPLEMENTED | M2 | TestGetConsoleGameHashes::test_raises_on_http_error |
| RA-DEV-023 | API | IMPLEMENTED | M2 | test_api_client.py |
| RA-DEV-024 | API | IMPLEMENTED | M3 | TestGetUserProgress |
| RA-DEV-025 | API | IMPLEMENTED | M3 | TestGetUserSummary |
| RA-DEV-026 | API | BASELINED | M5 | — |
| RA-DEV-030 | CACHE | IMPLEMENTED | M2 | test_cache.py |
| RA-DEV-031 | CACHE | IMPLEMENTED | M2 | TestTTL |
| RA-DEV-032 | CACHE | IMPLEMENTED | M2 | TestGetConsoleGameHashes::test_force_refresh_bypasses_cache |
| RA-DEV-033 | CACHE | IMPLEMENTED | M2 | TestCorruptCache |
| RA-DEV-034 | CACHE | IMPLEMENTED | M2 | TestClearAll |
| RA-DEV-040 | STATS | IMPLEMENTED | M3 | test_stats.py |
| RA-DEV-041 | STATS | IMPLEMENTED | M3 | TestEnrichWithProgress::test_unmatched_rom_gets_unmatched_status |
| RA-DEV-042 | STATS | IMPLEMENTED | M3 | TestGetCompletionLabel |
| RA-DEV-043 | STATS | IMPLEMENTED | M3 | TestEnrichWithProgress::test_api_error_sets_error_status |
| RA-DEV-050 | OUT | IMPLEMENTED | M4 | test_exporter.py |
| RA-DEV-051 | OUT | IMPLEMENTED | M4 | TestSummarySheet |
| RA-DEV-052 | OUT | IMPLEMENTED | M4 | TestConsoleSheet |
| RA-DEV-053 | OUT | IMPLEMENTED | M4 | TestSheetStructure::test_want_to_play_sheet_exists |
| RA-DEV-054 | OUT | BASELINED | M5 | — |
| RA-DEV-055 | OUT | DEFERRED | — | — |
| RA-DEV-060 | SYS | IMPLEMENTED | M1 | CI pipeline |
| RA-DEV-061 | SYS | IMPLEMENTED | M1 | CI pipeline (Python 3.12) |
| RA-DEV-062 | SYS | IMPLEMENTED | M4 | local run on Windows |
| RA-DEV-063 | SYS | IMPLEMENTED | M1 | .devcontainer |
| RA-DEV-064 | SYS | IMPLEMENTED | M1 | .github/workflows/ci.yml |
| RA-DEV-065 | SYS | IMPLEMENTED | M1 | .env + .gitignore |
| RA-DEV-066 | SYS | IMPLEMENTED | M1 | CI pipeline (ruff check) |