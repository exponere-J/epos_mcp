import { validateOrThrow } from "../schema_runtime";

export function validateEnvelopeOrThrow(envelope: unknown) {
  // We intentionally validate against the short alias key.
  // The schema runtime aliases telemetry_envelope -> core.telemetry_envelope.
  validateOrThrow("telemetry_envelope", envelope);
}
