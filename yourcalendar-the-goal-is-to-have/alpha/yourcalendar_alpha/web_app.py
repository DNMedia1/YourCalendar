from __future__ import annotations

import base64
import html
import json
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, urlparse

from .mapping import CalendarEntry, GroupLogo, load_group_logos, load_mapping
from .settings import load_settings, resolve_path


@dataclass
class TreeNode:
    name: str
    path: str
    depth: int = 0
    children: dict[str, "TreeNode"] = field(default_factory=dict)
    entries: list[CalendarEntry] = field(default_factory=list)


def build_tree(entries: list[CalendarEntry]) -> dict[str, TreeNode]:
    categories: dict[str, TreeNode] = {}
    for entry in entries:
        category_node = categories.setdefault(entry.category, TreeNode(entry.category, "", 0))
        current = category_node
        group_parts = entry.path_parts[:-1]
        for index, part in enumerate(group_parts, start=1):
            group_path = "/".join(group_parts[:index])
            current = current.children.setdefault(part, TreeNode(part, group_path, index))
        current.entries.append(entry)
    return categories


class CalendarRequestHandler(BaseHTTPRequestHandler):
    settings: dict[str, Any] = {}

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(render_index(self.settings))
            return
        if parsed.path.startswith("/ics/"):
            self._send_ics(parsed.path)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _send_html(self, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_ics(self, path: str) -> None:
        ics_name = Path(path).name
        ics_path = resolve_path(self.settings, self.settings["ics_output_dir"]) / ics_name
        if not ics_path.exists() or ics_path.suffix.lower() != ".ics":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        payload = ics_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/calendar; charset=utf-8")
        self.send_header("Content-Disposition", f'inline; filename="{ics_name}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def render_index(settings: dict[str, Any]) -> str:
    mapping_path = resolve_path(settings, settings["mapping_file"])
    group_logo_path = resolve_path(settings, settings["group_logo_settings_file"])
    entries = load_mapping(mapping_path)
    group_logos = load_group_logos(group_logo_path)
    tree = build_tree(entries)
    body = "\n".join(render_category(category, node, settings, group_logos) for category, node in sorted(tree.items()))
    title = html.escape(settings.get("site_title", "YourCalendar Alpha"))
    calendar_count = sum(len(node.entries) for node in iter_nodes(tree.values()))
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <script>
    const savedTheme = localStorage.getItem('yc-theme');
    const preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = savedTheme || preferredTheme;
  </script>
  <style>{CSS}</style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand-block">
        <div class="brand-mark" aria-hidden="true">YC</div>
        <div>
          <p class="product">YourCalendar</p>
          <h1>{title}</h1>
          <p class="tagline">Automatisch aktualisierte Kalender zum Abonnieren.</p>
        </div>
      </div>
      <dl class="summary">
        <div><dt>Kategorien</dt><dd>{len(tree)}</dd></div>
        <div><dt>Kalender</dt><dd>{calendar_count}</dd></div>
      </dl>
      <button class="theme-toggle" type="button" data-theme-toggle aria-label="Darkmode umschalten" title="Darkmode umschalten">
        <span class="theme-icon" aria-hidden="true"></span>
        <span class="theme-label">Darkmode</span>
      </button>
    </div>
  </header>
  <main class="shell">
    {body}
  </main>
  <dialog id="subscribeDialog">
    <form method="dialog" class="dialog">
      <div class="dialog-head">
        <div>
          <p class="eyebrow">Kalender abonnieren</p>
          <h2 id="dialogTitle">Kalender</h2>
        </div>
        <button class="icon-button" value="cancel" aria-label="Schliessen">x</button>
      </div>
      <div class="actions">
        <a id="googleLink" class="action" target="_blank" rel="noreferrer">Google Calendar</a>
        <a id="outlookLink" class="action" target="_blank" rel="noreferrer">Outlook</a>
        <a id="appleLink" class="action">Apple Calendar</a>
        <a id="icsLink" class="action secondary">ICS-Datei</a>
      </div>
    </form>
  </dialog>
  <script>{JS}</script>
</body>
</html>"""


def iter_nodes(nodes: Iterable[TreeNode]) -> list[TreeNode]:
    found: list[TreeNode] = []
    for node in nodes:
        found.append(node)
        found.extend(iter_nodes(node.children.values()))
    return found


def render_category(
    category: str,
    node: TreeNode,
    settings: dict[str, Any],
    group_logos: dict[tuple[str, str], GroupLogo],
) -> str:
    content = render_node_content(category, node, settings, group_logos)
    return f"""
<section class="category">
  <div class="category-head">
    <p class="eyebrow">Kategorie</p>
    <h2>{html.escape(category)}</h2>
  </div>
  {content}
</section>"""


def render_node_content(
    category: str,
    node: TreeNode,
    settings: dict[str, Any],
    group_logos: dict[tuple[str, str], GroupLogo],
) -> str:
    group_tiles = [
        render_group_tile(category, child, settings, group_logos)
        for child in sorted(node.children.values(), key=lambda item: group_sort_key(category, item, group_logos))
    ]
    entry_tiles = [
        render_calendar_tile(entry, settings)
        for entry in sorted(node.entries, key=lambda item: (item.subgroup_order, item.display_name))
    ]
    if not group_tiles and not entry_tiles:
        return ""
    return f"""
<div class="tile-grid" style="--level: {node.depth}">{"".join(group_tiles)}{"".join(entry_tiles)}</div>"""


def group_sort_key(
    category: str,
    node: TreeNode,
    group_logos: dict[tuple[str, str], GroupLogo],
) -> tuple[int, str]:
    logo = group_logos.get((category, node.path))
    order = logo.group_order if logo else 999_999
    return order, node.name


def render_group_tile(
    category: str,
    node: TreeNode,
    settings: dict[str, Any],
    group_logos: dict[tuple[str, str], GroupLogo],
) -> str:
    logo = group_logos.get((category, node.path))
    child_content = render_node_content(category, node, settings, group_logos)
    item_count = count_calendar_entries(node)
    return f"""
<details class="group-panel" style="--level: {node.depth}">
  <summary class="tile group-tile">
    {render_logo(logo.logo_bytes if logo else None, node.name)}
    <span class="tile-copy">
      <span class="eyebrow">Gruppe · {item_count} Kalender</span>
      <span class="group-title">{html.escape(node.name)}</span>
      <span class="group-path">{html.escape(node.path.replace("/", " / "))}</span>
    </span>
    <span class="chevron" aria-hidden="true">›</span>
  </summary>
  <div class="group-content">{child_content}</div>
</details>"""


def count_calendar_entries(node: TreeNode) -> int:
    return len(node.entries) + sum(count_calendar_entries(child) for child in node.children.values())


def render_calendar_tile(entry: CalendarEntry, settings: dict[str, Any]) -> str:
    public_url = calendar_public_url(settings, entry.ics_id)
    payload = {
        "name": entry.display_name,
        "ics": public_url,
        "google": f"https://calendar.google.com/calendar/r?cid={quote(public_url, safe='')}",
        "outlook": (
            "https://outlook.live.com/calendar/0/addcalendar"
            f"?url={quote(public_url, safe='')}&name={quote(entry.display_name, safe='')}"
        ),
        "apple": public_url.replace("http://", "webcal://").replace("https://", "webcal://", 1),
    }
    return f"""
<article class="tile calendar-tile">
  {render_logo(entry.logo_bytes, entry.display_name)}
  <div class="tile-copy">
    <p class="eyebrow">{html.escape(entry.country)} / {html.escape(entry.competition)}</p>
    <h3>{html.escape(entry.display_name)}</h3>
  </div>
  <button class="subscribe-button" data-subscribe='{html.escape(json.dumps(payload), quote=True)}'>Abonnieren</button>
</article>"""


def render_logo(logo_bytes: bytes | None, label: str) -> str:
    if logo_bytes:
        data_url = "data:image/png;base64," + base64.b64encode(logo_bytes).decode("ascii")
        return f'<img class="logo" src="{data_url}" alt="">'
    initials = "".join(part[0:1].upper() for part in label.split()[:2]) or "YC"
    return f'<div class="logo fallback" aria-hidden="true">{html.escape(initials)}</div>'


def calendar_public_url(settings: dict[str, Any], ics_id: str) -> str:
    base_url = str(settings.get("public_base_url") or "").rstrip("/")
    safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in ics_id)
    return f"{base_url}/ics/{quote(safe_id)}.ics"


def main() -> int:
    settings = load_settings()
    handler = CalendarRequestHandler
    handler.settings = settings
    host = str(settings.get("host", "127.0.0.1"))
    port = int(settings.get("port", 8080))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving YourCalendar Alpha at http://{host}:{port}")
    server.serve_forever()
    return 0


CSS = """
:root {
  color-scheme: light;
  --ink: #111827;
  --muted: #667085;
  --line: #d0d5dd;
  --line-soft: #eaecf0;
  --panel: #ffffff;
  --group: #f8fafc;
  --accent: #155eef;
  --accent-strong: #0f46b8;
  --surface: #f4f6f8;
  --shadow: 0 1px 2px rgba(16, 24, 40, 0.06), 0 8px 24px rgba(16, 24, 40, 0.06);
}
[data-theme="dark"] {
  color-scheme: dark;
  --ink: #f8fafc;
  --muted: #a8b3c4;
  --line: #334155;
  --line-soft: #243044;
  --panel: #111827;
  --group: #0f172a;
  --accent: #7dd3fc;
  --accent-strong: #38bdf8;
  --surface: #070b12;
  --shadow: 0 1px 2px rgba(0, 0, 0, 0.35), 0 14px 34px rgba(0, 0, 0, 0.28);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  background: var(--surface);
  color: var(--ink);
}
.topbar {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 251, 0.96)),
    #ffffff;
  border-bottom: 1px solid var(--line);
  padding: 18px 24px;
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
  box-shadow: 0 1px 0 rgba(16, 24, 40, 0.04);
}
[data-theme="dark"] .topbar {
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.94)),
    #0f172a;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04);
}
.topbar-inner {
  width: min(1180px, 100%);
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.brand-block {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 14px;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  background: var(--ink);
  color: #fff;
  font-weight: 800;
  letter-spacing: 0;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.16);
}
[data-theme="dark"] .brand-mark {
  background: #e5e7eb;
  color: #111827;
}
.product {
  margin: 0 0 4px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
}
.topbar h1 {
  margin: 0;
  font-size: 26px;
  line-height: 1.15;
}
.tagline {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.35;
}
.summary {
  display: flex;
  gap: 10px;
  margin: 0;
}
.summary div {
  min-width: 112px;
  padding: 11px 13px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
[data-theme="dark"] .summary div {
  background: rgba(17, 24, 39, 0.82);
}
.theme-toggle {
  min-height: 42px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 0 13px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}
[data-theme="dark"] .theme-toggle {
  background: rgba(17, 24, 39, 0.82);
}
.theme-icon {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 2px solid currentColor;
  display: inline-block;
  position: relative;
}
.theme-icon::after {
  content: "";
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  right: -3px;
  top: -3px;
  background: var(--surface);
}
[data-theme="dark"] .theme-icon::after {
  display: none;
}
.summary dt {
  color: var(--muted);
  font-size: 12px;
}
.summary dd {
  margin: 2px 0 0;
  font-size: 20px;
  font-weight: 700;
}
.shell {
  width: min(1180px, calc(100% - 32px));
  margin: 26px auto 52px;
}
.category { margin-bottom: 34px; }
.category-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}
.category h2 {
  font-size: 24px;
  margin: 0;
}
.tile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  align-items: stretch;
  margin-bottom: 18px;
}
.tile-grid.has-open > .group-panel:not([open]),
.tile-grid.has-open > .calendar-tile {
  display: none;
}
.tile {
  min-height: 166px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--panel);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow);
}
.group-tile {
  background: var(--group);
  box-shadow: none;
  cursor: pointer;
  list-style: none;
  min-height: 144px;
  position: relative;
}
.group-tile::-webkit-details-marker { display: none; }
.group-panel {
  display: block;
}
.group-panel[open] {
  grid-column: 1 / -1;
}
.group-content {
  margin: 14px 0 4px;
  padding-left: min(22px, calc(var(--level, 0) * 8px + 10px));
  border-left: 1px solid var(--line-soft);
}
.group-title {
  display: block;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
.group-path {
  display: block;
  margin-top: 6px;
  color: var(--muted);
  font-size: 13px;
  overflow-wrap: anywhere;
}
.chevron {
  position: absolute;
  right: 16px;
  top: 16px;
  width: 28px;
  height: 28px;
  border: 1px solid var(--line);
  border-radius: 999px;
  display: grid;
  place-items: center;
  color: var(--muted);
  font-size: 20px;
  line-height: 1;
}
.group-panel[open] > .group-tile .chevron {
  transform: rotate(90deg);
}
.calendar-tile { justify-content: space-between; }
.logo {
  width: 52px;
  height: 52px;
  border-radius: 8px;
  object-fit: contain;
  border: 1px solid var(--line-soft);
  background: #fff;
  flex: 0 0 auto;
}
[data-theme="dark"] .logo {
  background: #0b1220;
}
.fallback {
  display: grid;
  place-items: center;
  font-weight: 700;
  color: var(--ink);
  background: #f2f4f7;
}
[data-theme="dark"] .fallback {
  background: #1e293b;
}
.tile-copy {
  min-width: 0;
}
.tile-copy h3 {
  overflow-wrap: anywhere;
}
.eyebrow {
  margin: 0 0 4px;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  font-weight: 700;
}
h3 {
  margin: 0;
  font-size: 18px;
  line-height: 1.25;
}
.subscribe-button,
.action,
.icon-button {
  min-height: 40px;
  border-radius: 6px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
}
.subscribe-button:hover,
.action:hover { background: var(--accent-strong); }
.subscribe-button:focus-visible,
.action:focus-visible,
.icon-button:focus-visible {
  outline: 3px solid rgba(21, 94, 239, 0.25);
  outline-offset: 2px;
}
.action.secondary {
  background: #fff;
  color: var(--ink);
  border-color: var(--line);
}
[data-theme="dark"] .action.secondary,
[data-theme="dark"] .icon-button {
  background: #0f172a;
}
dialog {
  width: min(520px, calc(100% - 32px));
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0;
  background: var(--panel);
  color: var(--ink);
}
dialog::backdrop { background: rgba(17, 24, 39, 0.42); }
.dialog { padding: 20px; }
.dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.dialog h2 {
  margin: 0;
  font-size: 22px;
}
.icon-button {
  width: 36px;
  min-height: 36px;
  padding: 0;
  background: #fff;
  color: var(--ink);
  border-color: var(--line);
}
.actions {
  display: grid;
  gap: 10px;
}
@media (max-width: 720px) {
  .topbar {
    position: static;
    padding: 18px 14px;
  }
  .topbar-inner {
    align-items: stretch;
    flex-direction: column;
    gap: 14px;
  }
  .brand-block {
    align-items: flex-start;
  }
  .brand-mark {
    width: 42px;
    height: 42px;
  }
  .topbar h1 {
    font-size: 22px;
  }
  .summary {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .theme-toggle {
    justify-content: center;
    width: 100%;
  }
  .summary div { min-width: 0; }
  .shell {
    width: calc(100% - 24px);
    margin-top: 16px;
  }
  .level {
    padding-left: 0;
  }
  .group-content {
    padding-left: 10px;
  }
  .tile-grid {
    grid-template-columns: 1fr;
  }
  .tile {
    min-height: 144px;
  }
}
"""


JS = """
const dialog = document.getElementById('subscribeDialog');
const title = document.getElementById('dialogTitle');
const googleLink = document.getElementById('googleLink');
const outlookLink = document.getElementById('outlookLink');
const appleLink = document.getElementById('appleLink');
const icsLink = document.getElementById('icsLink');
const themeToggle = document.querySelector('[data-theme-toggle]');
const themeLabel = document.querySelector('.theme-label');

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('yc-theme', theme);
  if (themeLabel) {
    themeLabel.textContent = theme === 'dark' ? 'Lightmode' : 'Darkmode';
  }
  if (themeToggle) {
    themeToggle.setAttribute('aria-pressed', String(theme === 'dark'));
  }
}

setTheme(document.documentElement.dataset.theme || 'light');

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  });
}

document.querySelectorAll('[data-subscribe]').forEach((button) => {
  button.addEventListener('click', () => {
    const payload = JSON.parse(button.dataset.subscribe);
    title.textContent = payload.name;
    googleLink.href = payload.google;
    outlookLink.href = payload.outlook;
    appleLink.href = payload.apple;
    icsLink.href = payload.ics;
    dialog.showModal();
  });
});

document.querySelectorAll('.group-panel').forEach((panel) => {
  panel.addEventListener('toggle', () => {
    const grid = panel.parentElement;
    if (!grid || !grid.classList.contains('tile-grid')) {
      return;
    }
    if (panel.open) {
      grid.querySelectorAll(':scope > .group-panel[open]').forEach((sibling) => {
        if (sibling !== panel) {
          closeGroupTree(sibling);
        }
      });
      grid.classList.add('has-open');
    } else if (!grid.querySelector(':scope > .group-panel[open]')) {
      closeDescendantGroups(panel);
      grid.classList.remove('has-open');
    }
  });
});

function closeGroupTree(panel) {
  closeDescendantGroups(panel);
  panel.open = false;
}

function closeDescendantGroups(panel) {
  panel.querySelectorAll('.group-panel[open]').forEach((child) => {
    child.open = false;
  });
  panel.querySelectorAll('.tile-grid.has-open').forEach((grid) => {
    grid.classList.remove('has-open');
  });
}
"""


if __name__ == "__main__":
    raise SystemExit(main())
