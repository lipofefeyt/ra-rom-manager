import pandas as pd
import pytest

import src.ra_manager.cache as cache_module
from src.ra_manager.dashboard import create_app


class _FakeThread:
    """Replaces threading.Thread in tests — runs nothing, avoids subprocess."""
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_module, "DB_FILE", tmp_path / "test.db")
    monkeypatch.setattr(cache_module, "_LEGACY_JSON", tmp_path / "cache.json")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Flask test client with data dir redirected to tmp_path."""
    monkeypatch.chdir(tmp_path)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _write_xlsx(tmp_path: object, df: pd.DataFrame, sheet: str = "GBA") -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with pd.ExcelWriter(data_dir / "ra_collection.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet, index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Summary", index=False)


_SAMPLE_DF = pd.DataFrame(
    {
        "filename": ["Metroid Fusion.gba", "Unknown.gba"],
        "console": ["gba", "gba"],
        "ra_title": ["Metroid Fusion", ""],
        "matched": [True, False],
        "earned": [20, 0],
        "total": [40, 0],
        "completion_pct": [50.0, 0.0],
        "is_mastered": [False, False],
        "status": ["In Progress (20/40)", "Unmatched"],
        "ra_game_id": [1, None],
    }
)


class TestSummaryRoute:
    def test_returns_200_no_data(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_shows_no_file_message_when_missing(self, client):
        resp = client.get("/")
        assert b"No ra_collection.xlsx" in resp.data

    def test_returns_200_with_data(self, client, tmp_path):
        _write_xlsx(tmp_path, _SAMPLE_DF)
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Total ROMs" in resp.data

    def test_stat_cards_present(self, client, tmp_path):
        _write_xlsx(tmp_path, _SAMPLE_DF)
        resp = client.get("/")
        assert b"Matched" in resp.data
        assert b"Mastered" in resp.data


class TestConsoleRoute:
    def test_returns_200_with_data(self, client, tmp_path):
        _write_xlsx(tmp_path, _SAMPLE_DF)
        resp = client.get("/console/gba")
        assert resp.status_code == 200
        assert b"Metroid Fusion" in resp.data

    def test_unknown_console_shows_empty_message(self, client, tmp_path):
        _write_xlsx(tmp_path, _SAMPLE_DF)
        resp = client.get("/console/nes")
        assert resp.status_code == 200
        assert b"No ROMs found" in resp.data

    def test_no_data_returns_200(self, client):
        resp = client.get("/console/gba")
        assert resp.status_code == 200


class TestUnmatchedRoute:
    def test_returns_200_no_data(self, client):
        resp = client.get("/unmatched")
        assert resp.status_code == 200

    def test_shows_empty_message_when_no_sheet(self, client, tmp_path):
        _write_xlsx(tmp_path, _SAMPLE_DF)
        resp = client.get("/unmatched")
        assert resp.status_code == 200

    def test_shows_rows_when_sheet_present(self, client, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        unmatched_df = pd.DataFrame(
            {
                "Original Filename": ["Unknown.gba"],
                "Console": ["GBA"],
                "Suggested Title": ["Metroid Fusion"],
                "Expected Dump Name": ["Metroid Fusion (USA).gba"],
                "Patch URL": [""],
            }
        )
        with pd.ExcelWriter(data_dir / "ra_collection.xlsx", engine="openpyxl") as writer:
            _SAMPLE_DF.to_excel(writer, sheet_name="GBA", index=False)
            unmatched_df.to_excel(writer, sheet_name="Unmatched ROMs", index=False)
        resp = client.get("/unmatched")
        assert resp.status_code == 200
        assert b"Unknown.gba" in resp.data


class TestRescanRoute:
    def test_post_rescan_returns_202(self, client, monkeypatch):
        monkeypatch.setattr("src.ra_manager.dashboard.threading.Thread", _FakeThread)
        resp = client.post("/rescan")
        assert resp.status_code == 202
        assert resp.get_json()["status"] == "started"

    def test_post_rescan_returns_409_when_already_running(self, client, monkeypatch):
        import src.ra_manager.dashboard as dash
        dash._scan_state["running"] = True
        resp = client.post("/rescan")
        assert resp.status_code == 409
        assert resp.get_json()["status"] == "already_running"
        dash._scan_state["running"] = False

    def test_rescan_status_returns_expected_fields(self, client):
        resp = client.get("/rescan/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "running" in data
        assert "last_ran" in data
        assert "last_result" in data
        assert "message" in data

    def test_rescan_button_in_nav(self, client):
        resp = client.get("/")
        assert b"rescan-btn" in resp.data
        assert b"/rescan" in resp.data


class TestWantToPlayRoute:
    def test_returns_200_no_csv(self, client):
        resp = client.get("/wanttoplay")
        assert resp.status_code == 200
        assert b"No data/want_to_play.csv" in resp.data

    def test_shows_rows_when_csv_present(self, client, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        (data_dir / "want_to_play.csv").write_text(
            "ra_game_id,title,console,notes,added_date,owned\n"
            "1448,Rayman,GBA,,2024-01-01,No\n",
            encoding="utf-8",
        )
        resp = client.get("/wanttoplay")
        assert resp.status_code == 200
        assert b"Rayman" in resp.data
