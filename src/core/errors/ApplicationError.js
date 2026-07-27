export class ApplicationError extends Error {
  constructor(message, options = {}) {
    super(message, { cause: options.cause });
    this.name = this.constructor.name;
    this.code = options.code ?? "APPLICATION_ERROR";
  }
}

export class ValidationError extends ApplicationError {
  constructor(message, options = {}) {
    super(message, { ...options, code: "VALIDATION_ERROR" });
  }
}
