import json
import sqlite3
import time
from pathlib import Path

DB_FILE = Path("data/ra_cache.db")
_LEGACY_JSON = Path("data/cache.json")

# TTL values in seconds
TTL_HASH_LIST = 24 * 3600  # 24 hours - hash lists rarely change
TTL_USER_PROGRESS = 1 * 3600  # 1 hour - progress changes as you play


def _connect() -> sqlite3.Connection:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "CREATE TABLE IF NOT EXISTS cache "
        "(key TEXT PRIMARY KEY, value TEXT, updated_at REAL)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS runs "
        "(id INTEGER PRIMARY KEY, ran_at REAL, "
        "total_roms INTEGER, matched INTEGER, mastered INTEGER)"
    )
    con.commit()
    _migrate_json(con)
    return con


def _migrate_json(con: sqlite3.Connection) -> None:
    if not _LEGACY_JSON.exists():
        return
    try:
        data = json.loads(_LEGACY_JSON.read_text(encoding="utf-8"))
        for key, entry in data.items():
            con.execute(
                "INSERT OR IGNORE INTO cache(key, value, updated_at) VALUES (?,?,?)",
                (key, json.dumps(entry["value"]), entry.get("timestamp", time.time())),
            )
        con.commit()
        _LEGACY_JSON.rename(_LEGACY_JSON.with_suffix(".json.bak"))
    except Exception:
        pass


def load_cached(key: str, ttl: int) -> list | dict | None:
    """Returns the cached value for key if within TTL, else None."""
    try:
        with _connect() as con:
            row = con.execute(
                "SELECT value, updated_at FROM cache WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return None
        value_str, updated_at = row
        if time.time() - updated_at > ttl:
            return None
        return json.loads(value_str)
    except Exception:
        return None


def save_to_cache(key: str, value: list | dict) -> None:
    """Stores value under key with the current timestamp."""
    try:
        with _connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO cache(key, value, updated_at) VALUES (?,?,?)",
                (key, json.dumps(value), time.time()),
            )
    except Exception:
        pass


def record_run(total_roms: int, matched: int, mastered: int) -> None:
    """Appends a row to the runs table after each standard run."""
    try:
        with _connect() as con:
            con.execute(
                "INSERT INTO runs(ran_at, total_roms, matched, mastered) VALUES (?,?,?,?)",
                (time.time(), total_roms, matched, mastered),
            )
    except Exception:
        pass


def invalidate(key: str) -> None:
    """Removes a single key from the cache."""
    try:
        with _connect() as con:
            con.execute("DELETE FROM cache WHERE key=?", (key,))
    except Exception:
        pass


def clear_all() -> None:
    """Drops and recreates both tables, effectively wiping the cache."""
    try:
        with _connect() as con:
            con.execute("DROP TABLE IF EXISTS cache")
            con.execute("DROP TABLE IF EXISTS runs")
        # Re-create tables on next access
        _connect().close()
    except Exception:
        pass
