"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SchemaRuntimeError = void 0;
class SchemaRuntimeError extends Error {
    code;
    details;
    constructor(code, message, details) {
        super(message);
        this.name = "SchemaRuntimeError";
        this.code = code;
        this.details = details;
    }
}
exports.SchemaRuntimeError = SchemaRuntimeError;
//# sourceMappingURL=errors.js.map