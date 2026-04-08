"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateEnvelopeOrThrow = validateEnvelopeOrThrow;
const schema_runtime_1 = require("../schema_runtime");
function validateEnvelopeOrThrow(envelope) {
    // We intentionally validate against the short alias key.
    // The schema runtime aliases telemetry_envelope -> core.telemetry_envelope.
    (0, schema_runtime_1.validateOrThrow)("telemetry_envelope", envelope);
}
//# sourceMappingURL=validate.js.map