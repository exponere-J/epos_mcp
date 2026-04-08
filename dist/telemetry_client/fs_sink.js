"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.mkdirp = mkdirp;
exports.appendNdjsonLine = appendNdjsonLine;
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
function mkdirp(dir) {
    node_fs_1.default.mkdirSync(dir, { recursive: true });
}
function appendNdjsonLine(filePath, lineObj) {
    const dir = node_path_1.default.dirname(filePath);
    mkdirp(dir);
    node_fs_1.default.appendFileSync(filePath, JSON.stringify(lineObj) + "\n", "utf-8");
}
//# sourceMappingURL=fs_sink.js.map