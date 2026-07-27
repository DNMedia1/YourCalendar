import { IncomingLinkResolver } from "../linking/IncomingLinkResolver.js";
import { LogHandler } from "../logging/LogHandler.js";
import { CryptoWorkflow } from "./CryptoWorkflow.js";

export class AlphaBrowserWorkflow {
  constructor(options = {}) {
    this.logHandler = options.logHandler ?? new LogHandler();
    this.linkResolver = options.linkResolver ?? new IncomingLinkResolver();
    this.cryptoWorkflow =
      options.cryptoWorkflow ?? new CryptoWorkflow({ logHandler: this.logHandler });
  }

  resolveStartupValue(incomingUrl) {
    const value = this.linkResolver.resolveStartupValue(incomingUrl);
    this.logHandler.info("startup value resolved", { hasIncomingUrl: Boolean(incomingUrl) });
    return value;
  }

  resolveIncomingValue(incomingUrl) {
    const value = this.linkResolver.resolveIncomingValue(incomingUrl);
    this.logHandler.info("incoming value resolved", { hasIncomingValue: Boolean(value) });
    return value;
  }

  async encryptValue(value) {
    return this.cryptoWorkflow.encryptValue(value);
  }

  async decryptValue(value) {
    return this.cryptoWorkflow.decryptValue(value);
  }
}
