from __future__ import annotations

import base64
import html


def render_logo(logo_bytes: bytes | None, label: str) -> str:
    if logo_bytes:
        data_url = "data:image/png;base64," + base64.b64encode(logo_bytes).decode("ascii")
        return f'<img class="logo" src="{data_url}" alt="">'
    initials = "".join(part[0:1].upper() for part in label.split()[:2]) or "YC"
    return f'<div class="logo fallback" aria-hidden="true">{html.escape(initials)}</div>'
