import { LogHandler } from "../logging/LogHandler.js";
import { ValueValidator } from "../validation/ValueValidator.js";
import { PlaceholderTransformEngine } from "./PlaceholderTransformEngine.js";

export class CryptoWorkflow {
  constructor(options = {}) {
    this.validator = options.validator ?? new ValueValidator();
    this.transformEngine = options.transformEngine ?? new PlaceholderTransformEngine();
    this.logHandler = options.logHandler ?? new LogHandler();
  }

  async encryptValue(value) {
    return this.runTransform("encrypt", value);
  }

  async decryptValue(value) {
    return this.runTransform("decrypt", value);
  }

  async runTransform(transformName, value) {
    this.validator.assertValid(value);
    this.logHandler.info(`${transformName} workflow started`);

    try {
      const output = await this.transformEngine[transformName](value);
      this.logHandler.info(`${transformName} workflow completed`);
      return output;
    } catch (error) {
      this.logHandler.error(`${transformName} workflow failed`, error);
      throw error;
    }
  }
}
