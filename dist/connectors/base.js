"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.fingerprint = fingerprint;
const node_crypto_1 = __importDefault(require("node:crypto"));
function fingerprint(obj) {
    const raw = JSON.stringify(obj);
    return node_crypto_1.default.createHash("sha256").update(raw, "utf-8").digest("hex").slice(0, 16);
}
//# sourceMappingURL=base.js.map