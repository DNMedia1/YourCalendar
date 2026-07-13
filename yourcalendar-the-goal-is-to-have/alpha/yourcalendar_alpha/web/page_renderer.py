from __future__ import annotations

import html
from typing import Any

from ..calendar.tree_builder import build_calendar_tree, walk_calendar_tree
from ..config.settings import resolve_path
from ..mapping import load_group_logos, load_mapping
from .pages import STATIC_PAGES
from .rendering import render_category_section, render_document, render_footer, render_subscribe_dialog


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
