export class PlaceholderTransformEngine {
  async encrypt(value) {
    return this.createPendingOutput("Encrypted", value);
  }

  async decrypt(value) {
    return this.createPendingOutput("Decrypted", value);
  }

  createPendingOutput(actionName, value) {
    return [
      `${actionName} value`,
      "",
      "The workflow is connected, but no encryption or decryption mechanism is implemented in this alpha.",
      "",
      value
    ].join("\n");
  }
}
