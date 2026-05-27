import { readFile } from "node:fs/promises";
import { test } from "node:test";
import assert from "node:assert/strict";
import axe from "axe-core";
import { JSDOM } from "jsdom";

test("static shell passes axe-core smoke checks", async () => {
  const html = await readFile(new URL("../web/index.html", import.meta.url), "utf8");
  const dom = new JSDOM(html, {
    url: "http://127.0.0.1:8765/",
    runScripts: "outside-only",
    pretendToBeVisual: true,
  });

  dom.window.eval(axe.source);
  const results = await dom.window.axe.run(dom.window.document, {
    rules: {
      "color-contrast": { enabled: false },
    },
  });

  assert.equal(results.violations.length, 0, JSON.stringify(results.violations, null, 2));
});
