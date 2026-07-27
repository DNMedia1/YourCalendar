export class LogHandler {
  constructor(options = {}) {
    this.sink = options.sink ?? console;
    this.clock = options.clock ?? (() => new Date());
  }

  info(message, context = {}) {
    this.write("info", message, context);
  }

  warning(message, context = {}) {
    this.write("warning", message, context);
  }

  error(message, error, context = {}) {
    this.write("error", message, {
      ...context,
      error: this.serializeError(error)
    });
  }

  write(level, message, context = {}) {
    const entry = this.createEntry(level, message, context);
    const writer = this.sink[level] ?? this.sink.log ?? (() => undefined);
    writer.call(this.sink, JSON.stringify(entry));
  }

  createEntry(level, message, context) {
    return {
      level,
      message,
      context,
      createdAt: this.clock().toISOString()
    };
  }

  serializeError(error) {
    if (!error) {
      return undefined;
    }

    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
      code: error.code
    };
  }
}
