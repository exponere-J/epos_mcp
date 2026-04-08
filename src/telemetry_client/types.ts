export type TelemetryLevel = "debug" | "info" | "warn" | "error";

export type TelemetryEvent = {
  name: string;
  level: TelemetryLevel;
  fields: Record<string, unknown>;
};

export type TelemetryEnvelope = {
  schema_id: "core.telemetry_envelope";
  ts: string;
  run_id: string;
  event: TelemetryEvent;
};

export type TelemetryRunOptions = {
  runDir: string;
  runId: string;
};

export type TelemetryRun = {
  getEnvelope(): { run_id: string; run_dir: string };
  emit(event: TelemetryEvent): void;
  flush(): Promise<void>;
};
