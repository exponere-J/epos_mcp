"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAjvStrict = createAjvStrict;
const _2020_1 = __importDefault(require("ajv/dist/2020"));
const ajv_formats_1 = __importDefault(require("ajv-formats"));
function createAjvStrict() {
    const ajv = new _2020_1.default({
        strict: true,
        allErrors: true,
        allowUnionTypes: true
    });
    (0, ajv_formats_1.default)(ajv);
    return ajv;
}
//# sourceMappingURL=ajv_factory.js.map