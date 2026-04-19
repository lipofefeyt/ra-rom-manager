import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.ra_manager.api_client import RAClient, RAClientError

FIXTURES = Path("tests/fixtures/mock_ra_data.json")


@pytest.fixture
def mock_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.fixture
def client(monkeypatch, tmp_path):
    """RAClient with env vars set and cache redirected to tmp dir."""
    monkeypatch.setenv("RA_USERNAME", "testuser")
    monkeypatch.setenv("RA_API_KEY", "testapikey")
    import src.ra_manager.cache as cache_module

    monkeypatch.setattr(cache_module, "CACHE_FILE", tmp_path / "cache.json")
    return RAClient()


def _mock_response(data: dict | list, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        mock.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock)
    return mock


class TestGetConsoleGameHashes:
    def test_returns_game_list_from_api(self, client, mock_data):
        game_list = mock_data["console_4_games"]
        with patch("requests.get", return_value=_mock_response(game_list)):
            result = client.get_console_game_hashes(4)
        assert result == game_list

    def test_result_is_cached_after_first_call(self, client, mock_data):
        game_list = mock_data["console_4_games"]
        with patch("requests.get", return_value=_mock_response(game_list)) as mock_get:
            client.get_console_game_hashes(4)
            client.get_console_game_hashes(4)  # second call
        mock_get.assert_called_once()  # API called only once

    def test_force_refresh_bypasses_cache(self, client, mock_data):
        game_list = mock_data["console_4_games"]
        with patch("requests.get", return_value=_mock_response(game_list)) as mock_get:
            client.get_console_game_hashes(4)
            client.get_console_game_hashes(4, force_refresh=True)
        assert mock_get.call_count == 2

    def test_raises_on_timeout(self, client):
        with patch("requests.get", side_effect=requests.exceptions.Timeout):
            with pytest.raises(RAClientError, match="timed out"):
                client.get_console_game_hashes(4)

    def test_raises_on_http_error(self, client):
        with patch("requests.get", return_value=_mock_response({}, status_code=403)):
            with pytest.raises(RAClientError):
                client.get_console_game_hashes(4)


class TestGetUserProgress:
    def _api_response(self, earned: int, total: int) -> dict:
        """Build a minimal API_GetGameInfoAndUserProgress response."""
        achievements = {}
        for i in range(total):
            achievements[str(i)] = {
                "Points": 10,
                "DateEarned": "2024-01-01" if i < earned else None,
                "DateEarnedHardcore": None,
            }
        return {"Achievements": achievements}

    def test_returns_correct_earned_count(self, client):
        with patch("requests.get", return_value=_mock_response(self._api_response(15, 50))):
            result = client.get_user_progress(1141)
        assert result["earned"] == 15
        assert result["total"] == 50

    def test_mastered_when_all_earned(self, client):
        with patch("requests.get", return_value=_mock_response(self._api_response(10, 10))):
            result = client.get_user_progress(1448)
        assert result["is_mastered"] is True

    def test_not_mastered_when_partial(self, client):
        with patch("requests.get", return_value=_mock_response(self._api_response(5, 10))):
            result = client.get_user_progress(1141)
        assert result["is_mastered"] is False

    def test_result_is_cached(self, client):
        with patch(
            "requests.get", return_value=_mock_response(self._api_response(5, 10))
        ) as mock_get:
            client.get_user_progress(1141)
            client.get_user_progress(1141)
        mock_get.assert_called_once()


class TestGetUserSummary:
    def test_returns_correct_points(self, client):
        api_data = {"TotalPoints": 4200, "TotalSoftcorePoints": 300, "Rank": 18500, "NumGames": 42}
        with patch("requests.get", return_value=_mock_response(api_data)):
            result = client.get_user_summary()
        assert result["points"] == 4200
        assert result["rank"] == 18500

    def test_result_is_cached(self, client):
        api_data = {"TotalPoints": 100, "TotalSoftcorePoints": 0, "Rank": 999, "NumGames": 5}
        with patch("requests.get", return_value=_mock_response(api_data)) as mock_get:
            client.get_user_summary()
            client.get_user_summary()
        mock_get.assert_called_once()

class TestGetGameHashes:
    def test_returns_expected_format(self, client):
        api_data =[{
            "MD5": "1bc674be034e43c96b86487ac69d9293",
            "Name": "Sonic The Hedgehog.md",
            "Labels": ["nointro"],
            "PatchUrl": None
        }]
        with patch("requests.get", return_value=_mock_response(api_data)):
            result = client.get_game_hashes(1)
            assert isinstance(result, list)
            assert result[0]["MD5"] == "1bc674be034e43c96b86487ac69d9293"

    def test_caches_result(self, client):
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            client.get_game_hashes(1)
            client.get_game_hashes(1)
        mock_get.assert_called_once()