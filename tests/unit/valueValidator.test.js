import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ValueValidator } from "../../src/core/validation/ValueValidator.js";

describe("ValueValidator", () => {
  it("accepts a non-empty value", () => {
    const validator = new ValueValidator();

    assert.equal(validator.validate("https://example.com").isValid, true);
  });

  it("rejects an empty value", () => {
    const validator = new ValueValidator();
    const result = validator.validate("   ");

    assert.equal(result.isValid, false);
    assert.equal(result.message, "Value is mandatory.");
  });
});
