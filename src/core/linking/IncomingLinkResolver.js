import { DEFAULT_VALUE } from "../appDefaults.js";

export class IncomingLinkResolver {
  constructor(options = {}) {
    this.defaultValue = options.defaultValue ?? DEFAULT_VALUE;
  }

  resolveStartupValue(incomingUrl) {
    return this.resolveIncomingValue(incomingUrl) ?? this.defaultValue;
  }

  resolveIncomingValue(incomingUrl) {
    if (!this.hasText(incomingUrl)) {
      return null;
    }

    const customSchemeValue = this.extractCustomSchemeValue(incomingUrl);
    return customSchemeValue ?? incomingUrl;
  }

  createCustomSchemeUrl(value) {
    return `msbrowser://open?url=${encodeURIComponent(value)}`;
  }

  extractCustomSchemeValue(incomingUrl) {
    if (!incomingUrl.startsWith("msbrowser://")) {
      return null;
    }

    try {
      const parsedUrl = new URL(incomingUrl);
      return parsedUrl.searchParams.get("url") ?? parsedUrl.searchParams.get("value");
    } catch {
      return null;
    }
  }

  hasText(value) {
    return typeof value === "string" && value.trim().length > 0;
  }
}
