from __future__ import annotations

import html
import json
from typing import Any

from ...calendar.subscription_links import build_subscription_links
from ...calendar.tree_builder import count_calendar_entries, sort_group_node
from ...domain.calendar_entry import CalendarEntry
from ...domain.calendar_tree_node import CalendarTreeNode
from ...domain.group_logo import GroupLogo
from .logo import render_logo


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
