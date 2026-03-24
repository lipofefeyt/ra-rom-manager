import json

import pytest

from src.ra_manager.cache import (
    clear_all,
    invalidate,
    load_cached,
    save_to_cache,
)

TTL_SHORT = 1  # 1 second, for TTL expiry tests


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    """Redirect cache file to a temp directory for every test."""
    import src.ra_manager.cache as cache_module

    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(cache_module, "CACHE_FILE", cache_file)
    return cache_file


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
        result = load_cached("does_not_exist", ttl=3600)
        assert result is None

    def test_multiple_keys_coexist(self):
        save_to_cache("key_a", {"a": 1})
        save_to_cache("key_b", {"b": 2})
        assert load_cached("key_a", ttl=3600) == {"a": 1}
        assert load_cached("key_b", ttl=3600) == {"b": 2}


class TestTTL:
    def test_fresh_entry_is_returned(self):
        save_to_cache("console_5", [{"ID": 2}])
        assert load_cached("console_5", ttl=3600) is not None

    def test_expired_entry_returns_none(self):
        save_to_cache("console_5", [{"ID": 2}])
        # Manually backdate the timestamp
        import src.ra_manager.cache as cache_module

        raw = json.loads(cache_module.CACHE_FILE.read_text())
        raw["console_5"]["timestamp"] -= 7200  # 2 hours ago
        cache_module.CACHE_FILE.write_text(json.dumps(raw))

        result = load_cached("console_5", ttl=3600)
        assert result is None


class TestInvalidate:
    def test_invalidate_removes_key(self):
        save_to_cache("progress_99", {"earned": 5})
        invalidate("progress_99")
        assert load_cached("progress_99", ttl=3600) is None

    def test_invalidate_missing_key_does_not_raise(self):
        invalidate("never_existed")  # should not raise


class TestClearAll:
    def test_clear_all_wipes_cache(self):
        save_to_cache("console_4", [{"ID": 1}])
        save_to_cache("progress_1", {"earned": 1})
        clear_all()
        assert load_cached("console_4", ttl=3600) is None
        assert load_cached("progress_1", ttl=3600) is None

    def test_clear_all_on_empty_cache_does_not_raise(self):
        clear_all()  # nothing to clear, should not raise


class TestCorruptCache:
    def test_corrupt_cache_file_returns_none(self, tmp_path, monkeypatch):
        import src.ra_manager.cache as cache_module

        cache_module.CACHE_FILE.write_text("not valid json", encoding="utf-8")
        result = load_cached("any_key", ttl=3600)
        assert result is None
