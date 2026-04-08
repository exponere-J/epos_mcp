import fs from "node:fs";
import path from "node:path";

export function mkdirp(dir: string): void {
  fs.mkdirSync(dir, { recursive: true });
}

export function appendNdjsonLine(filePath: string, lineObj: unknown): void {
  const dir = path.dirname(filePath);
  mkdirp(dir);
  fs.appendFileSync(filePath, JSON.stringify(lineObj) + "\n", "utf-8");
}

