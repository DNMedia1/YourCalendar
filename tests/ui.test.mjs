import { readFile } from "node:fs/promises";
import { test } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";

function makeEvents(count) {
  return Array.from({ length: count }, (_, index) => ({
    uid: `event-${index}`,
    title: `Team ${index} vs Team ${index + 1}`,
    homeTeam: `Team ${index}`,
    awayTeam: `Team ${index + 1}`,
    league: "bl2",
    leagueName: "2. Bundesliga",
    dateLabel: "26.05.2026",
    timeLabel: "20:30 CEST",
    location: "Teststadion",
  }));
}

function makeCalendarPayload() {
  return {
    ok: true,
    qualityLegend: [
      { id: "community", label: "Community", description: "Freie Quelle ohne SLA." },
      { id: "planned", label: "Geplant", description: "Noch ohne produktive Quelle." },
    ],
    sportsCoverage: { europeSports: [], globalCombatSports: [], championships: [] },
    sourcePlan: { total: 0, active: 0, needsWork: 0, items: [] },
    sourceMonitor: { total: 0, watching: 0, planned: 0, items: [] },
    categories: [
      {
        id: "sports",
        name: "Sport",
        description: "Spielpläne und Wettbewerbe.",
        calendarCount: 1,
        calendars: [
          {
            id: "football-germany",
            name: "YourCalendar German Football",
            description: "Bundesliga und Pokal aus OpenLigaDB.",
            sourceLabel: "OpenLigaDB, Community-Daten",
            hasFeed: true,
            feedUrl: "/feeds/football-germany.ics",
            subscribeUrl: "http://127.0.0.1:8765/feeds/football-germany.ics",
            status: "available",
            statusLabel: "Verfügbar",
            quality: {
              level: "community",
              label: "Community, kein SLA",
              updatedLabel: "Katalogstand 28.05.2026 18:48 CEST",
              updatePolicy: "Beim Abruf aktualisiert.",
              reliabilityNote: "Keine Echtzeitgarantie.",
              warnings: ["Anstoßzeiten prüfen."],
            },
          },
        ],
      },
      {
        id: "culture",
        name: "Kultur",
        description: "Kulturprogramme und Festivals.",
        calendarCount: 0,
        calendars: [],
      },
    ],
  };
}

async function loadApp({ events = [] } = {}) {
  const html = await readFile(new URL("../web/index.html", import.meta.url), "utf8");
  const script = await readFile(new URL("../web/app.js", import.meta.url), "utf8");
  const dom = new JSDOM(html, {
    url: "http://127.0.0.1:8765/",
    runScripts: "dangerously",
    pretendToBeVisual: true,
    beforeParse(window) {
      window.fetch = async (url) => {
        const path = String(url);
        if (path.includes("/api/calendars")) {
          return { json: async () => makeCalendarPayload() };
        }
        if (path.includes("/api/import-status")) {
          return { json: async () => ({ ok: true, sources: [] }) };
        }
        if (path.includes("/api/source-candidates")) {
          return { json: async () => ({ ok: true, candidates: [] }) };
        }
        return {
          json: async () => ({
            ok: true,
            mode: "sample",
            sourceNote: "Testdaten",
            events,
          }),
        };
      };
      window.matchMedia = () => ({
        matches: false,
        media: "(prefers-color-scheme: dark)",
        addEventListener() {},
        removeEventListener() {},
      });
    },
  });

  const node = dom.window.document.createElement("script");
  node.textContent = script;
  dom.window.document.body.appendChild(node);
  await new Promise((resolve) => dom.window.setTimeout(resolve, 0));
  await new Promise((resolve) => dom.window.setTimeout(resolve, 0));
  return dom;
}

test("dark-mode toggle updates html data-theme and aria state", async () => {
  const dom = await loadApp();
  const { document } = dom.window;
  const toggle = document.getElementById("themeToggle");

  assert.equal(document.documentElement.dataset.theme, "light");
  assert.equal(toggle.getAttribute("aria-pressed"), "false");

  toggle.click();
  assert.equal(document.documentElement.dataset.theme, "dark");
  assert.equal(toggle.getAttribute("aria-pressed"), "true");
  assert.equal(toggle.getAttribute("aria-label"), "Light Mode aktivieren");
});

test("primary interactive controls expose accessible labels or text", async () => {
  const dom = await loadApp();
  const { document } = dom.window;
  const controls = [
    document.getElementById("themeToggle"),
    document.getElementById("refreshButton"),
    document.getElementById("appleButton"),
    document.getElementById("teamSearch"),
  ];

  for (const control of controls) {
    const accessibleText = [
      control.getAttribute("aria-label"),
      control.textContent,
      control.getAttribute("placeholder"),
    ].filter(Boolean).join(" ").trim();

    assert.notEqual(accessibleText, "");
  }
});

test("event list exposes accessible empty and busy states", async () => {
  const dom = await loadApp();
  const { document } = dom.window;
  const eventList = document.getElementById("eventList");
  const emptyState = eventList.querySelector(".empty-state");

  assert.equal(eventList.getAttribute("aria-busy"), "false");
  assert.equal(emptyState.getAttribute("role"), "status");
  assert.match(emptyState.textContent, /Keine Spiele/);
});

test("calendar discovery renders public category and subscription context", async () => {
  const dom = await loadApp();
  const { document } = dom.window;

  assert.match(document.querySelector(".catalog-intro").textContent, /ohne Login/);
  assert.match(document.getElementById("categoryOverview").textContent, /Sport/);
  assert.match(document.getElementById("categoryOverview").textContent, /1 von 1 abonnierbar/);
  assert.match(document.getElementById("calendarCatalog").textContent, /OpenLigaDB/);
  assert.match(document.getElementById("calendarCatalog").textContent, /Apple Kalender/);
  assert.match(document.getElementById("calendarCatalog").textContent, /Google per URL/);
  assert.match(document.getElementById("calendarCatalog").textContent, /Outlook aus dem Internet/);
});

test("long event lists render a capped visible set", async () => {
  const dom = await loadApp({ events: makeEvents(250) });
  const { document } = dom.window;

  assert.equal(document.querySelectorAll(".event-card").length, 200);
  assert.match(document.querySelector(".list-note").textContent, /200 von 250/);
});

test("frontend assets stay within the current performance budget", async () => {
  const budgets = [
    ["../web/app.js", 32000],
    ["../web/styles.css", 30000],
    ["../web/mobile.css", 6000],
    ["../web/tailwind.css", 10000],
  ];

  let totalBytes = 0;
  for (const [path, maxBytes] of budgets) {
    const file = await readFile(new URL(path, import.meta.url));
    totalBytes += file.byteLength;
    assert.ok(file.byteLength <= maxBytes, `${path} exceeds ${maxBytes} bytes`);
  }
  assert.ok(totalBytes <= 75000, `frontend assets exceed 75000 bytes: ${totalBytes}`);
});
