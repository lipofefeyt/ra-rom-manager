import json
import time
from pathlib import Path

CACHE_FILE = Path("data/cache.json")

# TTL values in seconds
TTL_HASH_LIST = 24 * 3600  # 24 hours — hash lists rarely change
TTL_USER_PROGRESS = 1 * 3600  # 1 hour — progress changes as you play


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(data: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_cached(key: str, ttl: int) -> list | dict | None:
    """
    Returns the cached value for key if it exists and is within TTL.
    Returns None if the key is missing or stale.
    """
    data = _load_cache()
    entry = data.get(key)
    if entry is None:
        return None
    if time.time() - entry["timestamp"] > ttl:
        return None
    return entry["value"]


def save_to_cache(key: str, value: list | dict) -> None:
    """Stores value under key with the current timestamp."""
    data = _load_cache()
    data[key] = {"timestamp": time.time(), "value": value}
    _save_cache(data)


def invalidate(key: str) -> None:
    """Removes a single key from the cache."""
    data = _load_cache()
    if key in data:
        del data[key]
        _save_cache(data)


def clear_all() -> None:
    """Wipes the entire cache file."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    print("🗑️  Cache cleared.")
