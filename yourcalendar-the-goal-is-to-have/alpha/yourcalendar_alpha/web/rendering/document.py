from __future__ import annotations

import html

from ..pages import VISIBLE_FOOTER_LINKS


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
