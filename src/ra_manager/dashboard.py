"""
Local web dashboard - serves collection data from the SQLite cache.
Launch with: python main.py --serve
"""
import json
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify

from .cache import DB_FILE

_scan_state: dict = {
    "running": False,
    "last_ran": None,
    "last_result": None,
    "message": "",
}
_scan_lock = threading.Lock()


def _do_scan(cwd: Path | None = None) -> None:
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=cwd,
        )
        with _scan_lock:
            _scan_state["running"] = False
            _scan_state["last_ran"] = datetime.now().isoformat(timespec="seconds")
            if result.returncode == 0:
                _scan_state["last_result"] = "ok"
                _scan_state["message"] = "Scan completed successfully."
            else:
                tail = (result.stderr.strip() or result.stdout.strip())[-200:]
                _scan_state["last_result"] = "error"
                _scan_state["message"] = tail or "Unknown error."
    except subprocess.TimeoutExpired:
        with _scan_lock:
            _scan_state["running"] = False
            _scan_state["last_result"] = "error"
            _scan_state["message"] = "Scan timed out after 5 minutes."
    except Exception as e:  # noqa: BLE001
        with _scan_lock:
            _scan_state["running"] = False
            _scan_state["last_result"] = "error"
            _scan_state["message"] = str(e)

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RA ROM Manager - {title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  body{{font-family:Arial,sans-serif;margin:0;background:#f4f4f4;color:#222}}
  nav{{background:#1F4E79;padding:12px 24px;display:flex;gap:24px;align-items:center}}
  nav a{{color:#fff;text-decoration:none;font-weight:bold;font-size:14px}}
  nav a:hover{{text-decoration:underline}}
  nav .brand{{font-size:18px;margin-right:auto}}
  h1{{color:#1F4E79;margin:24px 24px 8px}}
  .cards{{display:flex;flex-wrap:wrap;gap:16px;padding:0 24px 16px}}
  .card{{background:#fff;border-radius:8px;padding:20px 28px;
         box-shadow:0 1px 4px #0002;min-width:140px}}
  .card .val{{font-size:32px;font-weight:bold;color:#1F4E79}}
  .card .lbl{{font-size:13px;color:#666;margin-top:4px}}
  .chart-row{{display:flex;gap:24px;padding:0 24px 24px;flex-wrap:wrap}}
  .chart-box{{background:#fff;border-radius:8px;padding:16px;
              box-shadow:0 1px 4px #0002;flex:1;min-width:280px;max-width:420px}}
  table{{width:calc(100% - 48px);margin:0 24px 24px;border-collapse:collapse;background:#fff;
         border-radius:8px;overflow:hidden;box-shadow:0 1px 4px #0002}}
  th{{background:#1F4E79;color:#fff;padding:10px 12px;text-align:left;font-size:13px}}
  td{{padding:8px 12px;font-size:13px;border-bottom:1px solid #eee}}
  tr:last-child td{{border-bottom:none}}
  tr.mastered{{background:#C6EFCE}}
  tr.progress{{background:#FFEB9C}}
  tr.unmatched{{background:#FFC7CE}}
  tr:nth-child(even){{background:#f9f9f9}}
  tr.mastered:nth-child(even){{background:#b8e8c0}}
  .badge{{display:inline-block;padding:2px 8px;border-radius:12px;
          font-size:11px;font-weight:bold}}
  .badge.m{{background:#C6EFCE;color:#276221}}
  .badge.p{{background:#FFEB9C;color:#7d6608}}
  .badge.u{{background:#FFC7CE;color:#9c1a1a}}
  a.patch{{color:#1F4E79;font-size:12px}}
  .empty{{padding:24px;color:#888;font-style:italic}}
  .rescan-btn{{background:#fff;color:#1F4E79;border:none;border-radius:4px;
               padding:6px 14px;font-weight:bold;font-size:13px;cursor:pointer}}
  .rescan-btn:disabled{{opacity:0.5;cursor:not-allowed}}
  .rescan-msg{{color:#fff;font-size:12px;margin-left:8px}}
</style>
</head>
<body>
<nav>
  <span class="brand">🎮 RA ROM Manager</span>
  <a href="/">Summary</a>
  {console_links}
  <a href="/unmatched">Unmatched</a>
  <a href="/wanttoplay">Want to Play</a>
  <button class="rescan-btn" id="rescan-btn" onclick="startRescan()">Rescan</button>
  <span class="rescan-msg" id="rescan-msg"></span>
</nav>
{body}
<script>
function startRescan(){{
  var btn=document.getElementById('rescan-btn');
  var msg=document.getElementById('rescan-msg');
  btn.disabled=true;
  msg.textContent='Starting…';
  fetch('/rescan',{{method:'POST'}}).then(function(){{pollRescan();}});
}}
function pollRescan(){{
  var btn=document.getElementById('rescan-btn');
  var msg=document.getElementById('rescan-msg');
  fetch('/rescan/status').then(function(r){{return r.json();}}).then(function(d){{
    if(d.running){{
      msg.textContent='⏳ Scanning…';
      setTimeout(pollRescan,2000);
    }}else{{
      btn.disabled=false;
      if(d.last_result==='ok'){{
        msg.textContent='✅ Done - reload to see updates';
      }}else if(d.last_result==='error'){{
        msg.textContent='❌ '+d.message;
      }}else{{
        msg.textContent='';
      }}
    }}
  }});
}}
</script>
</body></html>"""


def _nav_links(consoles: list[str]) -> str:
    return " ".join(
        f'<a href="/console/{c.lower()}">{c}</a>' for c in sorted(consoles)
    )


_XLSX_COL_RENAMES = {
    "Filename": "filename",
    "RA Title": "ra_title",
    "RA Game ID": "ra_game_id",
    "Matched": "matched",
    "Earned": "earned",
    "Total": "total",
    "Completion %": "completion_pct",
    "Mastered": "is_mastered",
    "Status": "status",
    "Console": "console",
}
_BOOL_COLS = {"matched", "is_mastered"}


def _load_xlsx() -> pd.DataFrame | None:
    xlsx = Path("data/ra_collection.xlsx")
    if not xlsx.exists():
        return None
    skip = {"Summary", "Unmatched ROMs", "Want to Play"}
    try:
        sheets = pd.read_excel(xlsx, sheet_name=None, engine="openpyxl")
        frames = []
        for name, df in sheets.items():
            if name in skip or df.empty:
                continue
            df = df.rename(columns=_XLSX_COL_RENAMES)
            for col in _BOOL_COLS:
                if col in df.columns:
                    df[col] = df[col].isin(["Yes", True, 1])
            frames.append(df)
        return pd.concat(frames, ignore_index=True) if frames else None
    except Exception:
        return None


def _run_history() -> list[dict]:
    if not DB_FILE.exists():
        return []
    try:
        with sqlite3.connect(DB_FILE) as con:
            rows = con.execute(
                "SELECT ran_at, total_roms, matched, mastered FROM runs ORDER BY ran_at"
            ).fetchall()
        return [
            {"ran_at": r[0], "total_roms": r[1], "matched": r[2], "mastered": r[3]}
            for r in rows
        ]
    except Exception:
        return []


def _consoles_from(df: pd.DataFrame | None) -> list[str]:
    if df is None or "console" not in df.columns:
        return []
    return sorted(df["console"].str.upper().unique().tolist())


def _row_classes(status: str) -> tuple[str, str]:
    if "Mastered" in status:
        return "mastered", "m"
    if "Progress" in status:
        return "progress", "p"
    if "Unmatched" in status:
        return "unmatched", "u"
    return "", ""


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def summary():
        df = _load_xlsx()
        if df is None:
            body = (
                '<p class="empty">No ra_collection.xlsx found. '
                "Run <code>python main.py</code> first.</p>"
            )
            return _TEMPLATE.format(title="Summary", console_links="", body=body)

        consoles = _consoles_from(df)
        total = len(df)
        matched = int(df["matched"].sum()) if "matched" in df.columns else 0
        mastered = int(df["is_mastered"].sum()) if "is_mastered" in df.columns else 0
        in_progress = (
            int(df["status"].str.startswith("In Progress").sum())
            if "status" in df.columns
            else 0
        )

        history = _run_history()
        chart_labels = json.dumps([str(i + 1) for i in range(len(history))])
        chart_mastered = json.dumps([r["mastered"] for r in history])
        chart_matched = json.dumps([r["matched"] for r in history])

        status_counts = df["status"].value_counts().to_dict() if "status" in df.columns else {}
        pie_labels = json.dumps(list(status_counts.keys()))
        pie_data = json.dumps([int(v) for v in status_counts.values()])

        console_counts = (
            df["console"].str.upper().value_counts().to_dict()
            if "console" in df.columns
            else {}
        )
        bar_labels = json.dumps(list(console_counts.keys()))
        bar_data = json.dumps([int(v) for v in console_counts.values()])

        unmatched = total - matched
        cards = (
            f'<div class="cards">'
            f'<div class="card"><div class="val">{total}</div>'
            f'<div class="lbl">Total ROMs</div></div>'
            f'<div class="card"><div class="val">{matched}</div>'
            f'<div class="lbl">Matched</div></div>'
            f'<div class="card"><div class="val">{unmatched}</div>'
            f'<div class="lbl">Unmatched</div></div>'
            f'<div class="card"><div class="val">{mastered}</div>'
            f'<div class="lbl">Mastered 🏆</div></div>'
            f'<div class="card"><div class="val">{in_progress}</div>'
            f'<div class="lbl">In Progress</div></div>'
            f"</div>"
        )

        hist_canvas = (
            '<div class="chart-box"><canvas id="hist"></canvas></div>'
            if history
            else ""
        )
        hist_script = (
            f"""
          new Chart(document.getElementById('hist'), {{
            type:'line',
            data:{{labels:{chart_labels},datasets:[
              {{label:'Mastered',data:{chart_mastered},
               borderColor:'#276221',tension:0.3,fill:false}},
              {{label:'Matched',data:{chart_matched},
               borderColor:'#1F4E79',tension:0.3,fill:false}}
            ]}},
            options:{{plugins:{{legend:{{position:'bottom'}}}}}}
          }});"""
            if history
            else ""
        )

        charts = f"""
        <div class="chart-row">
          <div class="chart-box"><canvas id="pie"></canvas></div>
          <div class="chart-box"><canvas id="bar"></canvas></div>
          {hist_canvas}
        </div>
        <script>
          new Chart(document.getElementById('pie'), {{
            type:'doughnut',
            data:{{labels:{pie_labels},datasets:[{{data:{pie_data},
              backgroundColor:['#C6EFCE','#FFEB9C','#FFC7CE','#BDD7EE','#ccc']}}]}},
            options:{{plugins:{{legend:{{position:'bottom'}}}}}}
          }});
          new Chart(document.getElementById('bar'), {{
            type:'bar',
            data:{{labels:{bar_labels},datasets:[{{label:'ROMs',data:{bar_data},
              backgroundColor:'#1F4E79'}}]}},
            options:{{plugins:{{legend:{{display:false}}}}}}
          }});
          {hist_script}
        </script>"""

        body = f"<h1>Collection Summary</h1>{cards}{charts}"
        return _TEMPLATE.format(
            title="Summary", console_links=_nav_links(consoles), body=body
        )

    @app.route("/console/<name>")
    def console_view(name: str):
        df = _load_xlsx()
        if df is None or "console" not in df.columns:
            return _TEMPLATE.format(
                title=name.upper(), console_links="", body='<p class="empty">No data.</p>'
            )

        consoles = _consoles_from(df)
        cdf = df[df["console"].str.upper() == name.upper()].copy()
        if cdf.empty:
            body = f'<p class="empty">No ROMs found for {name.upper()}.</p>'
            return _TEMPLATE.format(
                title=name.upper(), console_links=_nav_links(consoles), body=body
            )

        rows_html = ""
        for _, row in cdf.iterrows():
            status = str(row.get("status", ""))
            cls, badge_cls = _row_classes(status)
            pct = row.get("completion_pct", "")
            pct_str = f"{pct:.1f}%" if isinstance(pct, float) else ""
            rows_html += (
                f'<tr class="{cls}">'
                f"<td>{row.get('filename','')}</td>"
                f"<td>{row.get('ra_title','')}</td>"
                f"<td>{row.get('earned','')}</td>"
                f"<td>{row.get('total','')}</td>"
                f"<td>{pct_str}</td>"
                f'<td><span class="badge {badge_cls}">{status}</span></td>'
                f"</tr>"
            )

        header = (
            "<tr><th>Filename</th><th>RA Title</th>"
            "<th>Earned</th><th>Total</th><th>%</th><th>Status</th></tr>"
        )
        body = f"<h1>{name.upper()}</h1><table>{header}{rows_html}</table>"
        return _TEMPLATE.format(
            title=name.upper(), console_links=_nav_links(consoles), body=body
        )

    @app.route("/unmatched")
    def unmatched():
        xlsx = Path("data/ra_collection.xlsx")
        df = None
        if xlsx.exists():
            try:
                df = pd.read_excel(xlsx, sheet_name="Unmatched ROMs", engine="openpyxl")
            except Exception:
                pass

        consoles = _consoles_from(_load_xlsx())

        if df is None or df.empty:
            body = '<p class="empty">No unmatched ROMs - or run main.py first.</p>'
            return _TEMPLATE.format(
                title="Unmatched ROMs", console_links=_nav_links(consoles), body=body
            )

        rows_html = ""
        for _, row in df.iterrows():
            patch = row.get("Patch URL", "") or ""
            patch_link = (
                f'<a class="patch" href="{patch}" target="_blank">Download</a>'
                if patch
                else ""
            )
            rows_html += (
                "<tr>"
                f"<td>{row.get('Original Filename','')}</td>"
                f"<td>{row.get('Console','')}</td>"
                f"<td>{row.get('Suggested Title','')}</td>"
                f"<td>{row.get('Expected Dump Name','')}</td>"
                f"<td>{patch_link}</td>"
                "</tr>"
            )

        header = (
            "<tr><th>Filename</th><th>Console</th>"
            "<th>Suggested Title</th><th>Expected Dump</th><th>Patch</th></tr>"
        )
        body = f"<h1>Unmatched ROMs</h1><table>{header}{rows_html}</table>"
        return _TEMPLATE.format(
            title="Unmatched ROMs", console_links=_nav_links(consoles), body=body
        )

    @app.route("/wanttoplay")
    def want_to_play():
        wtp_path = Path("data/want_to_play.csv")
        consoles = _consoles_from(_load_xlsx())

        if not wtp_path.exists():
            body = '<p class="empty">No data/want_to_play.csv found.</p>'
            return _TEMPLATE.format(
                title="Want to Play", console_links=_nav_links(consoles), body=body
            )

        df = pd.read_csv(wtp_path)
        rows_html = ""
        for _, row in df.iterrows():
            rows_html += (
                "<tr>"
                f"<td>{row.get('ra_game_id','')}</td>"
                f"<td>{row.get('title','')}</td>"
                f"<td>{row.get('console','')}</td>"
                f"<td>{row.get('notes','')}</td>"
                f"<td>{row.get('added_date','')}</td>"
                f"<td>{row.get('owned','')}</td>"
                "</tr>"
            )

        header = (
            "<tr><th>ID</th><th>Title</th><th>Console</th>"
            "<th>Notes</th><th>Added</th><th>Owned</th></tr>"
        )
        body = f"<h1>Want to Play</h1><table>{header}{rows_html}</table>"
        return _TEMPLATE.format(
            title="Want to Play", console_links=_nav_links(consoles), body=body
        )

    @app.route("/rescan", methods=["POST"])
    def rescan():
        with _scan_lock:
            if _scan_state["running"]:
                return jsonify({"status": "already_running"}), 409
            _scan_state["running"] = True
            _scan_state["message"] = "Scanning…"
        cwd = Path(__file__).parent.parent.parent
        t = threading.Thread(target=_do_scan, args=(cwd,), daemon=True)
        t.start()
        return jsonify({"status": "started"}), 202

    @app.route("/rescan/status")
    def rescan_status():
        with _scan_lock:
            return jsonify(dict(_scan_state))

    return app


def serve(host: str = "127.0.0.1", port: int = 5000) -> None:
    app = create_app()
    print(f"🌐 Dashboard running at http://{host}:{port}  (Ctrl+C to stop)")
    app.run(host=host, port=port, debug=False)
