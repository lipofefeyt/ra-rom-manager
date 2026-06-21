import html
from pathlib import Path

import pandas as pd

HTML_OUTPUT_PATH = Path("data/ra_collection.html")

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; font-size: 14px; background: #f5f5f5; color: #222; }
.page { max-width: 1400px; margin: 0 auto; padding: 24px; }
h1 { color: #1F4E79; font-size: 22px; margin-bottom: 20px; }
h2 { color: #1F4E79; font-size: 16px; margin: 28px 0 10px; padding-bottom: 4px;
     border-bottom: 2px solid #1F4E79; }
.summary-grid { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 8px; }
.summary-card { background: #fff; border: 1px solid #ddd; border-radius: 6px;
                padding: 16px 22px; min-width: 180px; }
.summary-card .label { font-size: 12px; color: #666; margin-bottom: 4px; }
.summary-card .value { font-size: 22px; font-weight: bold; color: #1F4E79; }
table { width: 100%; border-collapse: collapse; background: #fff;
        border: 1px solid #ddd; border-radius: 4px; margin-bottom: 32px; }
thead th { background: #1F4E79; color: #fff; padding: 8px 10px;
           text-align: left; font-size: 12px; }
tbody td { padding: 7px 10px; font-size: 13px; border-top: 1px solid #eee; }
.row-mastered { background: #C6EFCE; }
.row-in-progress { background: #FFEB9C; }
.row-unmatched { background: #FFC7CE; }
.row-alt { background: #F2F2F2; }
a { color: #0563C1; }
.note { color: #999; font-style: italic; padding: 10px; }
.meta { color: #888; font-size: 12px; margin-bottom: 24px; }
"""


def _esc(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return html.escape(str(value))


def _row_class(status: str) -> str:
    if status == "Mastered 🏆":
        return "row-mastered"
    if str(status).startswith("In Progress"):
        return "row-in-progress"
    if status in ("Unknown/Unlinked", "Unmatched"):
        return "row-unmatched"
    return ""


def _card(label: str, value) -> str:
    return (
        f'<div class="summary-card">'
        f'<div class="label">{_esc(label)}</div>'
        f'<div class="value">{_esc(value)}</div>'
        f"</div>"
    )


def _summary_section(df: pd.DataFrame, user_summary: dict | None) -> str:
    total = len(df)
    matched = int(df["matched"].sum()) if "matched" in df.columns else 0
    mastered = int(df["is_mastered"].sum()) if "is_mastered" in df.columns else 0
    in_progress = (
        int(df["status"].str.startswith("In Progress").sum()) if "status" in df.columns else 0
    )
    unplayed = int((df["status"] == "Unplayed").sum()) if "status" in df.columns else 0
    match_rate = f"{matched / total * 100:.1f}%" if total else "-"

    parts = ['<h2>Collection</h2><div class="summary-grid">']
    parts.append(_card("Total ROMs", total))
    parts.append(_card("Matched to RA", matched))
    parts.append(_card("Match Rate", match_rate))
    parts.append(_card("Mastered 🏆", mastered))
    parts.append(_card("In Progress", in_progress))
    parts.append(_card("Unplayed", unplayed))
    parts.append("</div>")

    if user_summary:
        parts.append('<h2>RA Profile</h2><div class="summary-grid">')
        parts.append(_card("Points", user_summary.get("points", "-")))
        parts.append(_card("Softcore Points", user_summary.get("softcore_points", "-")))
        parts.append(_card("Global Rank", user_summary.get("rank", "-")))
        parts.append(_card("Games Played", user_summary.get("games_played", "-")))
        parts.append("</div>")

    return "\n".join(parts)


_CONSOLE_COLS = [
    ("Filename", "filename"),
    ("RA Title", "ra_title"),
    ("Matched", "matched"),
    ("Earned", "earned"),
    ("Total", "total"),
    ("Completion %", "completion_pct"),
    ("Mastered", "is_mastered"),
    ("Status", "status"),
]

_UNMATCHED_COLS = [
    ("Original Filename", "filename"),
    ("Console", "console"),
    ("Suggested Title", "suggested_title"),
    ("Expected Dump Name", "suggested_filename"),
    ("Expected MD5", "suggested_md5"),
    ("Patch URL", "patch_url"),
]

_WANT_TO_PLAY_COLS = [
    ("RA Game ID", "ra_game_id"),
    ("Title", "title"),
    ("Console", "console"),
    ("Notes", "notes"),
    ("Added Date", "added_date"),
    ("Owned", "owned"),
]


def _table(columns: list[tuple[str, str]], rows: list[dict], patch_url_col: str = "") -> str:
    headers = "".join(f"<th>{_esc(label)}</th>" for label, _ in columns)
    tbody_rows = []
    for i, row in enumerate(rows):
        status = str(row.get("status", ""))
        row_cls = _row_class(status) or ("row-alt" if i % 2 == 0 else "")
        cls_attr = f' class="{row_cls}"' if row_cls else ""
        cells = []
        for _, col_key in columns:
            value = row.get(col_key, "")
            if isinstance(value, bool):
                display = "Yes" if value else "No"
            elif value is None or (isinstance(value, float) and pd.isna(value)):
                display = ""
            else:
                display = str(value)

            if col_key == patch_url_col and display:
                cell_html = f'<a href="{_esc(display)}" target="_blank">Patch</a>'
            else:
                cell_html = _esc(display)

            cells.append(f"<td>{cell_html}</td>")
        tbody_rows.append(f"<tr{cls_attr}>{''.join(cells)}</tr>")

    return (
        f"<table><thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(tbody_rows)}</tbody></table>"
    )


def _console_sections(df: pd.DataFrame) -> str:
    parts = []
    consoles = sorted(df["console"].str.upper().unique()) if "console" in df.columns else []
    for console in consoles:
        console_df = df[df["console"].str.upper() == console]
        rows = console_df.to_dict(orient="records")
        parts.append(f"<h2>{_esc(console)}</h2>")
        parts.append(_table(_CONSOLE_COLS, rows))
    return "\n".join(parts)


def _unmatched_section(df: pd.DataFrame) -> str:
    unmatched_df = df[~df["matched"]] if "matched" in df.columns else df.iloc[0:0]
    parts = ["<h2>Unmatched ROMs</h2>"]
    if unmatched_df.empty:
        parts.append('<p class="note">All ROMs matched perfectly!</p>')
    else:
        rows = unmatched_df.to_dict(orient="records")
        parts.append(_table(_UNMATCHED_COLS, rows, patch_url_col="patch_url"))
    return "\n".join(parts)


def _want_to_play_section() -> str:
    want_to_play_path = Path("data/want_to_play.csv")
    parts = ["<h2>Want to Play</h2>"]
    if want_to_play_path.exists():
        wtp_df = pd.read_csv(want_to_play_path)
        rows = wtp_df.to_dict(orient="records")
        parts.append(_table(_WANT_TO_PLAY_COLS, rows))
    else:
        parts.append('<p class="note">No want_to_play.csv found in data/</p>')
    return "\n".join(parts)


def export_html(
    df: pd.DataFrame,
    user_summary: dict | None = None,
    output_path: Path | str | None = None,
) -> Path:
    target_path = Path(output_path) if output_path else HTML_OUTPUT_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    body = "\n".join([
        _summary_section(df, user_summary),
        _console_sections(df),
        _unmatched_section(df),
        _want_to_play_section(),
    ])

    html_doc = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>RA ROM Manager - Collection Report</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="page">\n'
        "<h1>RA ROM Manager - Collection Report</h1>\n"
        f"{body}\n"
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )

    target_path.write_text(html_doc, encoding="utf-8")
    return target_path
