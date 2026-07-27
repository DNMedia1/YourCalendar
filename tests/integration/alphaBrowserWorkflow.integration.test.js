import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { AlphaBrowserWorkflow } from "../../src/core/workflow/AlphaBrowserWorkflow.js";
import { IncomingLinkResolver } from "../../src/core/linking/IncomingLinkResolver.js";
import { LogHandler } from "../../src/core/logging/LogHandler.js";

describe("Alpha browser workflow", () => {
  it("prefills a link and returns encrypt and decrypt workflow output", async () => {
    const logs = [];
    const sink = {
      info: entry => logs.push(entry),
      warning: entry => logs.push(entry),
      error: entry => logs.push(entry),
      log: entry => logs.push(entry)
    };
    const workflow = new AlphaBrowserWorkflow({
      logHandler: new LogHandler({ sink }),
      linkResolver: new IncomingLinkResolver({ defaultValue: "https://" })
    });

    const startupValue = workflow.resolveStartupValue("https://openai.com");
    const encryptedValue = await workflow.encryptValue(startupValue);
    const decryptedValue = await workflow.decryptValue(startupValue);

    assert.equal(startupValue, "https://openai.com");
    assert.match(encryptedValue, /Encrypted value/);
    assert.match(decryptedValue, /Decrypted value/);
    assert.ok(logs.length >= 3);
  });
});
