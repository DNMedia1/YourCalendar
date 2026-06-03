from __future__ import annotations

import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from yourcalendar_alpha.web.http_handler import CalendarHttpRequestHandler


class WebHttpIntegrationTests(unittest.TestCase):
    def test_http_server_renders_mapping_entries_and_serves_ics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            ics_dir = root / "public" / "ics"
            data_dir.mkdir()
            ics_dir.mkdir(parents=True)
            (data_dir / "mapping.csv").write_text(
                "Kalendername,Land,Kategorie,Wettbewerb,API-Provider,API-Key-Provider,ICSId,LogoBytes,SubGroupOrder\n"
                "Fussball/Deutschland/1. Bundesliga/Test Team,Deutschland,Sport,1. Bundesliga,TheSportsDB,,42,,1\n",
                encoding="utf-8",
            )
            (data_dir / "group_logo_settings.csv").write_text(
                "Kategorie,GroupPath,LogoBytes,groupOrder\n"
                "Sport,Fussball,,1\n"
                "Sport,Fussball/Deutschland,,1\n"
                "Sport,Fussball/Deutschland/1. Bundesliga,,1\n",
                encoding="utf-8",
            )
            (ics_dir / "42.ics").write_text("BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", encoding="utf-8")

            handler = type("TestHandler", (CalendarHttpRequestHandler,), {})
            handler.settings = {
                "_root_dir": str(root),
                "site_title": "Test Calendar",
                "mapping_file": "data/mapping.csv",
                "group_logo_settings_file": "data/group_logo_settings.csv",
                "ics_output_dir": "public/ics",
                "public_base_url": "http://127.0.0.1",
            }
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                with urlopen(base_url, timeout=10) as response:
                    html = response.read().decode("utf-8")
                self.assertIn("Test Team", html)
                self.assertIn("Fussball / Deutschland / 1. Bundesliga", html)
                self.assertIn("<details", html)
                self.assertIn("<summary", html)
                self.assertIn("Google Calendar", html)
                self.assertIn("Outlook", html)
                self.assertIn("Apple Calendar", html)
                self.assertIn("ICS-Datei", html)
                self.assertIn('/static/site.css', html)
                self.assertIn('/static/site.js', html)
                self.assertIn('href="/impressum"', html)
                self.assertNotIn('href="/partnerships"', html)
                self.assertNotIn('href="/create-your-own-calendar"', html)

                with urlopen(f"{base_url}/static/site.css", timeout=10) as response:
                    content_type = response.headers["Content-Type"]
                    css_body = response.read().decode("utf-8")
                self.assertEqual(content_type, "text/css; charset=utf-8")
                self.assertIn(".topbar", css_body)

                with urlopen(f"{base_url}/static/site.js", timeout=10) as response:
                    content_type = response.headers["Content-Type"]
                    js_body = response.read().decode("utf-8")
                self.assertEqual(content_type, "text/javascript; charset=utf-8")
                self.assertIn("data-theme-toggle", js_body)

                with urlopen(f"{base_url}/impressum", timeout=10) as response:
                    impressum_body = response.read().decode("utf-8")
                self.assertIn("Impressum", impressum_body)

                with urlopen(f"{base_url}/partnerships", timeout=10) as response:
                    partnerships_body = response.read().decode("utf-8")
                self.assertIn("Partnerships", partnerships_body)

                with urlopen(f"{base_url}/create-your-own-calendar", timeout=10) as response:
                    create_calendar_body = response.read().decode("utf-8")
                self.assertIn("Create Your Own Calendar", create_calendar_body)

                with urlopen(f"{base_url}/ics/42.ics", timeout=10) as response:
                    content_type = response.headers["Content-Type"]
                    ics_body = response.read().decode("utf-8")
                self.assertEqual(content_type, "text/calendar; charset=utf-8")
                self.assertIn("BEGIN:VCALENDAR", ics_body)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
