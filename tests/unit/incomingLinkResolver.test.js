import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { IncomingLinkResolver } from "../../src/core/linking/IncomingLinkResolver.js";

describe("IncomingLinkResolver", () => {
  it("uses the default value when no link starts the app", () => {
    const resolver = new IncomingLinkResolver({ defaultValue: "https://" });

    assert.equal(resolver.resolveStartupValue(null), "https://");
  });

  it("uses an http link as the startup value", () => {
    const resolver = new IncomingLinkResolver();

    assert.equal(resolver.resolveStartupValue("https://example.com/a"), "https://example.com/a");
  });

  it("extracts a link from the app scheme", () => {
    const resolver = new IncomingLinkResolver();
    const appUrl = resolver.createCustomSchemeUrl("https://example.com/search?q=value");

    assert.equal(
      resolver.resolveStartupValue(appUrl),
      "https://example.com/search?q=value"
    );
  });
});
