import os
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, send_from_directory


DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
PNG_DIR = Path(os.getenv("PNG_DIR", DATA_DIR / "png"))
GALLERY_TITLE = os.getenv("GALLERY_TITLE", "SA8818 Panoramic RTL")
FILENAME_RE = re.compile(r"^(?P<station>.+)-(?P<start>\d{14})-(?P<stop>\d{14})$")

app = Flask(__name__)


def parse_item(path: Path) -> dict[str, str]:
    match = FILENAME_RE.match(path.stem)
    if match:
        start = datetime.strptime(match.group("start"), "%Y%m%d%H%M%S")
        stop = datetime.strptime(match.group("stop"), "%Y%m%d%H%M%S")
        station = match.group("station").upper()
        return {
            "file": path.name,
            "station": station,
            "start": start.strftime("%Y-%m-%d %H:%M:%S"),
            "stop": stop.strftime("%Y-%m-%d %H:%M:%S"),
            "title": f"{station}: {start:%Y-%m-%d %H:%M} - {stop:%H:%M}",
        }
    return {
        "file": path.name,
        "station": "",
        "start": "",
        "stop": "",
        "title": path.stem,
    }


def gallery_items() -> list[dict[str, str]]:
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    return [parse_item(path) for path in sorted(PNG_DIR.glob("*.png"), reverse=True)]


@app.get("/")
def index() -> str:
    items = gallery_items()
    cards = "\n".join(
        f"""
        <article class="card">
          <a href="/png/{item['file']}" target="_blank" rel="noopener">
            <img src="/png/{item['file']}" alt="{item['title']}">
          </a>
          <div class="meta">
            <strong>{item['title']}</strong>
            <span>{item['start']} - {item['stop']}</span>
          </div>
        </article>
        """
        for item in items
    )
    empty = "<p class=\"empty\">PNG heatmaps will appear here after the first capture is processed.</p>" if not items else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="60">
  <title>{GALLERY_TITLE}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #111317;
      --panel: #1a1f27;
      --text: #edf0f3;
      --muted: #aeb7c2;
      --line: #303846;
      --accent: #62c6a4;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      padding: 18px clamp(16px, 4vw, 40px);
      border-bottom: 1px solid var(--line);
      background: rgba(17, 19, 23, 0.94);
      backdrop-filter: blur(10px);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(20px, 3vw, 30px);
      font-weight: 700;
      letter-spacing: 0;
    }}
    .count {{
      color: var(--muted);
      white-space: nowrap;
    }}
    main {{
      padding: 24px clamp(16px, 4vw, 40px) 40px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr));
      gap: 18px;
    }}
    .card {{
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    .card img {{
      display: block;
      width: 100%;
      aspect-ratio: 16 / 9;
      object-fit: cover;
      background: #08090b;
    }}
    .meta {{
      display: grid;
      gap: 4px;
      padding: 12px 14px 14px;
    }}
    .meta strong {{
      overflow-wrap: anywhere;
      font-size: 15px;
    }}
    .meta span, .empty {{
      color: var(--muted);
      font-size: 14px;
    }}
    a:focus-visible {{
      outline: 2px solid var(--accent);
      outline-offset: 3px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{GALLERY_TITLE}</h1>
    <div class="count">{len(items)} heatmaps</div>
  </header>
  <main>
    {empty}
    <section class="grid">{cards}</section>
  </main>
</body>
</html>"""


@app.get("/png/<path:name>")
def png(name: str):
    return send_from_directory(PNG_DIR, name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
