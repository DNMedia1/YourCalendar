import { readFile } from "node:fs/promises";
import { test } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";

async function loadApp() {
  const html = await readFile(new URL("../web/index.html", import.meta.url), "utf8");
  const script = await readFile(new URL("../web/app.js", import.meta.url), "utf8");
  const dom = new JSDOM(html, {
    url: "http://127.0.0.1:8765/",
    runScripts: "dangerously",
    pretendToBeVisual: true,
    beforeParse(window) {
      window.fetch = async () => ({
        json: async () => ({
          ok: true,
          mode: "sample",
          sourceNote: "Testdaten",
          events: [],
        }),
      });
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
