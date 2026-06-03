from __future__ import annotations

import base64
import html
import json
from typing import Any

from ..calendar.subscription_links import build_subscription_links
from ..calendar.tree_builder import build_calendar_tree, count_calendar_entries, sort_group_node, walk_calendar_tree
from ..config.settings import resolve_path
from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_tree_node import CalendarTreeNode
from ..domain.group_logo import GroupLogo
from ..mapping import load_group_logos, load_mapping
from .pages import STATIC_PAGES, VISIBLE_FOOTER_LINKS


def render_home_page(settings: dict[str, Any]) -> str:
    mapping_path = resolve_path(settings, settings["mapping_file"])
    group_logo_path = resolve_path(settings, settings["group_logo_settings_file"])
    entries = load_mapping(mapping_path)
    group_logos = load_group_logos(group_logo_path)
    tree = build_calendar_tree(entries)
    category_sections = "\n".join(
        render_category_section(category, node, settings, group_logos) for category, node in sorted(tree.items())
    )
    page_title = html.escape(settings.get("site_title", "YourCalendar Alpha"))
    calendar_count = sum(len(node.entries) for node in walk_calendar_tree(tree.values()))
    return render_document(
        page_title=page_title,
        body=f"""
  <main class="shell">
    {category_sections}
  </main>
  {render_subscribe_dialog()}""",
        summary=f"""
      <dl class="summary">
        <div><dt>Kategorien</dt><dd>{len(tree)}</dd></div>
        <div><dt>Kalender</dt><dd>{calendar_count}</dd></div>
      </dl>""",
    )


def render_static_page(path: str, settings: dict[str, Any]) -> str | None:
    page = STATIC_PAGES.get(path)
    if not page:
        return None
    site_title = html.escape(settings.get("site_title", "YourCalendar Alpha"))
    page_title = html.escape(str(page["title"]))
    body = "\n".join(f"      <p>{html.escape(paragraph)}</p>" for paragraph in page["body"])
    return render_document(
        page_title=f"{page_title} - {site_title}",
        body=f"""
  <main class="shell static-page">
    <section class="static-content">
      <p class="eyebrow">{html.escape(str(page["eyebrow"]))}</p>
      <h2>{page_title}</h2>
{body}
    </section>
  </main>""",
    )


def render_document(page_title: str, body: str, summary: str = "") -> str:
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <link rel="stylesheet" href="/static/site.css">
  <script src="/static/site.js" defer></script>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand-block">
        <div class="brand-mark" aria-hidden="true">YC</div>
        <div>
          <p class="product">YourCalendar</p>
          <h1>{page_title}</h1>
          <p class="tagline">Automatisch aktualisierte Kalender zum Abonnieren.</p>
        </div>
      </div>
{summary}
      <button class="theme-toggle" type="button" data-theme-toggle aria-label="Darkmode umschalten" title="Darkmode umschalten">
        <span class="theme-icon" aria-hidden="true"></span>
        <span class="theme-label">Darkmode</span>
      </button>
    </div>
  </header>
{body}
  {render_footer()}
</body>
</html>"""


def render_footer() -> str:
    links = "\n".join(
        f'        <a href="{html.escape(href)}">{html.escape(label)}</a>' for href, label in VISIBLE_FOOTER_LINKS
    )
    return f"""
  <footer class="site-footer">
    <div class="site-footer-inner">
      <div>
        <p class="product">YourCalendar Alpha</p>
        <p class="footer-copy">Generische abonnierbare Kalender fuer automatisch aktualisierte ICS-Dateien.</p>
      </div>
      <nav class="footer-links" aria-label="Footer">
{links}
      </nav>
    </div>
  </footer>"""


def render_subscribe_dialog() -> str:
    return """
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
  </dialog>"""


def render_category_section(
    category: str,
    node: CalendarTreeNode,
    settings: dict[str, Any],
    group_logos: dict[tuple[str, str], GroupLogo],
) -> str:
    content = render_tile_grid(category, node, settings, group_logos)
    return f"""
<section class="category">
  <div class="category-head">
    <p class="eyebrow">Kategorie</p>
    <h2>{html.escape(category)}</h2>
  </div>
  {content}
</section>"""


def render_tile_grid(
    category: str,
    node: CalendarTreeNode,
    settings: dict[str, Any],
    group_logos: dict[tuple[str, str], GroupLogo],
) -> str:
    group_tiles = [
        render_group_tile(category, child, settings, group_logos)
        for child in sorted(node.children.values(), key=lambda item: sort_group_node(category, item, group_logos))
    ]
    calendar_tiles = [
        render_calendar_tile(entry, settings)
        for entry in sorted(node.entries, key=lambda item: (item.subgroup_order, item.display_name))
    ]
    if not group_tiles and not calendar_tiles:
        return ""
    return f"""
<div class="tile-grid" style="--level: {node.depth}">{"".join(group_tiles)}{"".join(calendar_tiles)}</div>"""


def render_group_tile(
    category: str,
    node: CalendarTreeNode,
    settings: dict[str, Any],
    group_logos: dict[tuple[str, str], GroupLogo],
) -> str:
    group_logo = group_logos.get((category, node.path))
    child_content = render_tile_grid(category, node, settings, group_logos)
    calendar_count = count_calendar_entries(node)
    return f"""
<details class="group-panel" style="--level: {node.depth}">
  <summary class="tile group-tile">
    {render_logo(group_logo.logo_bytes if group_logo else None, node.name)}
    <span class="tile-copy">
      <span class="eyebrow">Gruppe - {calendar_count} Kalender</span>
      <span class="group-title">{html.escape(node.name)}</span>
      <span class="group-path">{html.escape(node.path.replace("/", " / "))}</span>
    </span>
    <span class="chevron" aria-hidden="true">&gt;</span>
  </summary>
  <div class="group-content">{child_content}</div>
</details>"""


def render_calendar_tile(entry: CalendarEntry, settings: dict[str, Any]) -> str:
    payload = build_subscription_links(entry, settings)
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
