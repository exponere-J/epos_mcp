export type SchemaErrorCode = "SCHEMA_NOT_FOUND" | "SCHEMA_INVALID" | "DATA_INVALID";

export class SchemaRuntimeError extends Error {
  public readonly code: SchemaErrorCode;
  public readonly details?: unknown;

  constructor(code: SchemaErrorCode, message: string, details?: unknown) {
    super(message);
    this.code = code;
    this.details = details;
  }
}
