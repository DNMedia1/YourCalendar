from __future__ import annotations

from collections.abc import Iterable

from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_tree_node import CalendarTreeNode
from ..domain.group_logo import GroupLogo


def build_calendar_tree(entries: list[CalendarEntry]) -> dict[str, CalendarTreeNode]:
    categories: dict[str, CalendarTreeNode] = {}
    for entry in entries:
        category_node = categories.setdefault(entry.category, CalendarTreeNode(entry.category, "", 0))
        current_node = category_node
        group_parts = entry.path_parts[:-1]
        for index, part in enumerate(group_parts, start=1):
            group_path = "/".join(group_parts[:index])
            current_node = current_node.children.setdefault(part, CalendarTreeNode(part, group_path, index))
        current_node.entries.append(entry)
    return categories


def walk_calendar_tree(nodes: Iterable[CalendarTreeNode]) -> list[CalendarTreeNode]:
    found_nodes: list[CalendarTreeNode] = []
    for node in nodes:
        found_nodes.append(node)
        found_nodes.extend(walk_calendar_tree(node.children.values()))
    return found_nodes


def count_calendar_entries(node: CalendarTreeNode) -> int:
    return len(node.entries) + sum(count_calendar_entries(child) for child in node.children.values())


def sort_group_node(
    category: str,
    node: CalendarTreeNode,
    group_logos: dict[tuple[str, str], GroupLogo],
) -> tuple[int, str]:
    group_logo = group_logos.get((category, node.path))
    group_order = group_logo.group_order if group_logo else 999_999
    return group_order, node.name
