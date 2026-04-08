export type SchemaRuntimeErrorCode = "SCHEMA_INVALID" | "SCHEMA_NOT_FOUND" | "DATA_INVALID";

export class SchemaRuntimeError extends Error {
  public readonly code: SchemaRuntimeErrorCode;
  public readonly details?: Record<string, unknown>;

  constructor(code: SchemaRuntimeErrorCode, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "SchemaRuntimeError";
    this.code = code;
    this.details = details;
  }
}
