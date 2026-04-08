import fs from "node:fs";
import path from "node:path";

import type { TelemetryEnvelope, TelemetryEvent, TelemetryRun, TelemetryRunOptions } from "./types";
import { appendNdjsonLine, mkdirp } from "./fs_sink";
import { validateEnvelopeOrThrow } from "./validate";

function isoNow(): string {
  return new Date().toISOString();
}

function defaultRunId(): string {
  // deterministic enough for tests; real system can swap later
  return `run_${Date.now()}`;
}

function defaultRunDir(runId: string): string {
  return path.join(process.cwd(), "runs", runId);
}

export function createTelemetryRun(opts?: Partial<TelemetryRunOptions>): TelemetryRun {
  const runId = opts?.runId ?? defaultRunId();
  const runDir = opts?.runDir ?? defaultRunDir(runId);

  const telemetryFile = path.join(runDir, "telemetry.json");

  // Track whether a completion has already been emitted (manual or automatic)
  let completionSeen = false;

  // Ensure runDir exists (binding)
  try {
    mkdirp(runDir);
  } catch (e) {
    // best-effort; continue
    // eslint-disable-next-line no-console
    console.error("TELEMETRY_WRITE_FAILED", String((e as any)?.message ?? e));
  }

  const emit = (event: TelemetryEvent): void => {
    if (event?.name === "system.run_completed") {
      completionSeen = true;
    }

    const envelope: TelemetryEnvelope = {
      schema_id: "core.telemetry_envelope",
      ts: isoNow(),
      run_id: runId,
      event,
    };

    // Validate by schemaId constant (binding)
    validateEnvelopeOrThrow(envelope);

    // Write NDJSON line (binding). If write fails, log + continue.
    try {
      appendNdjsonLine(telemetryFile, envelope);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error("TELEMETRY_WRITE_FAILED", String((e as any)?.message ?? e));
    }
  };

  const flush = async (): Promise<void> => {
    // Binding: flush emits system.run_completed only if not already present
    if (!completionSeen) {
      emit({
        name: "system.run_completed",
        level: "info",
        fields: {},
      });
      completionSeen = true;
    }
  };

  return {
    getEnvelope(): { run_id: string; run_dir: string } {
      return { run_id: runId, run_dir: runDir };
    },
    emit,
    flush,
  };
}


