from __future__ import annotations


def provider_lock_changed(current: list[dict[str, str]], generated: list[dict[str, str]]) -> bool:
    return bool(current and current != generated)


def print_provider_lock_diff(current: list[dict[str, str]], generated: list[dict[str, str]]) -> None:
    current_by_key = {(row["Team"], row["Provider"]): row for row in current}
    generated_by_key = {(row["Team"], row["Provider"]): row for row in generated}
    for key in sorted(set(current_by_key) | set(generated_by_key)):
        old = current_by_key.get(key)
        new = generated_by_key.get(key)
        if old != new:
            print(f"- {key[0]} / {key[1]}: {old} -> {new}")
