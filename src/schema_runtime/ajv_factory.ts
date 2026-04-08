import Ajv2020 from "ajv/dist/2020";
import addFormats from "ajv-formats";

export function createAjvStrict() {
  const ajv = new Ajv2020({
    strict: true,
    allErrors: true,
    allowUnionTypes: true
  });

  addFormats(ajv);
  return ajv;
}
