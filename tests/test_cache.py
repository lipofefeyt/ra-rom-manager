import sqlite3
import time

import pytest

from src.ra_manager.cache import (
    clear_all,
    invalidate,
    load_cached,
    record_run,
    save_to_cache,
)

TTL_SHORT = 1


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Redirect DB_FILE to a temp directory for every test."""
    import src.ra_manager.cache as cache_module

    db = tmp_path / "test_cache.db"
    monkeypatch.setattr(cache_module, "DB_FILE", db)
    monkeypatch.setattr(cache_module, "_LEGACY_JSON", tmp_path / "cache.json")
    return db


class TestSaveAndLoad:
    def test_save_and_load_list(self):
        save_to_cache("console_4", [{"ID": 1, "Title": "Rayman"}])
        result = load_cached("console_4", ttl=3600)
        assert result == [{"ID": 1, "Title": "Rayman"}]

    def test_save_and_load_dict(self):
        data = {"earned": 15, "total": 50}
        save_to_cache("progress_1141", data)
        result = load_cached("progress_1141", ttl=3600)
        assert result == data

    def test_missing_key_returns_none(self):
        assert load_cached("does_not_exist", ttl=3600) is None

    def test_multiple_keys_coexist(self):
        save_to_cache("key_a", {"a": 1})
        save_to_cache("key_b", {"b": 2})
        assert load_cached("key_a", ttl=3600) == {"a": 1}
        assert load_cached("key_b", ttl=3600) == {"b": 2}


class TestTTL:
    def test_fresh_entry_is_returned(self):
        save_to_cache("console_5", [{"ID": 2}])
        assert load_cached("console_5", ttl=3600) is not None

    def test_expired_entry_returns_none(self, tmp_db):
        save_to_cache("console_5", [{"ID": 2}])
        # Backdate updated_at directly in SQLite
        with sqlite3.connect(tmp_db) as con:
            con.execute(
                "UPDATE cache SET updated_at=? WHERE key=?",
                (time.time() - 7200, "console_5"),
            )
        assert load_cached("console_5", ttl=3600) is None


class TestInvalidate:
    def test_invalidate_removes_key(self):
        save_to_cache("progress_99", {"earned": 5})
        invalidate("progress_99")
        assert load_cached("progress_99", ttl=3600) is None

    def test_invalidate_missing_key_does_not_raise(self):
        invalidate("never_existed")


class TestClearAll:
    def test_clear_all_wipes_cache(self):
        save_to_cache("console_4", [{"ID": 1}])
        save_to_cache("progress_1", {"earned": 1})
        clear_all()
        assert load_cached("console_4", ttl=3600) is None
        assert load_cached("progress_1", ttl=3600) is None

    def test_clear_all_on_empty_cache_does_not_raise(self):
        clear_all()


class TestCorruptCache:
    def test_corrupt_db_file_returns_none(self, tmp_db):
        tmp_db.write_bytes(b"not a sqlite database")
        assert load_cached("any_key", ttl=3600) is None


class TestRecordRun:
    def test_record_run_writes_row(self, tmp_db):
        record_run(total_roms=100, matched=80, mastered=5)
        with sqlite3.connect(tmp_db) as con:
            row = con.execute(
                "SELECT total_roms, matched, mastered FROM runs"
            ).fetchone()
        assert row == (100, 80, 5)

    def test_multiple_runs_all_stored(self, tmp_db):
        record_run(10, 8, 1)
        record_run(12, 10, 2)
        with sqlite3.connect(tmp_db) as con:
            count = con.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        assert count == 2


class TestJSONMigration:
    def test_migrates_legacy_json_on_first_connect(self, tmp_db, tmp_path, monkeypatch):
        import json

        import src.ra_manager.cache as cache_module

        legacy = tmp_path / "cache.json"
        legacy.write_text(
            json.dumps({"console_4": {"timestamp": time.time(), "value": [{"ID": 99}]}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(cache_module, "_LEGACY_JSON", legacy)

        result = load_cached("console_4", ttl=3600)
        assert result == [{"ID": 99}]
        assert legacy.with_suffix(".json.bak").exists()
        assert not legacy.exists()
