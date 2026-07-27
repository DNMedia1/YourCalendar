import { ValidationError } from "../errors/ApplicationError.js";

export class ValueValidator {
  validate(value) {
    if (!this.hasValue(value)) {
      return {
        isValid: false,
        message: "Value is mandatory."
      };
    }

    return {
      isValid: true,
      message: ""
    };
  }

  assertValid(value) {
    const result = this.validate(value);

    if (!result.isValid) {
      throw new ValidationError(result.message);
    }
  }

  hasValue(value) {
    return typeof value === "string" && value.trim().length > 0;
  }
}
