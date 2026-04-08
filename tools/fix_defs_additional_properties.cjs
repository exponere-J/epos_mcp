const fs = require("fs");
const path = require("path");

const p = path.join(process.cwd(), "schemas", "__defs.schema.json");
if (!fs.existsSync(p)) {
  console.error("Missing schemas/__defs.schema.json");
  process.exit(1);
}

const json = JSON.parse(fs.readFileSync(p, "utf-8"));

if (json.type === "object" || json.$defs || json.definitions || json.properties) {
  if (json.additionalProperties === undefined) {
    json.additionalProperties = false;
    fs.writeFileSync(p, JSON.stringify(json, null, 2) + "\n", "utf-8");
    console.log("Updated schemas/__defs.schema.json: added additionalProperties:false");
  } else {
    console.log("schemas/__defs.schema.json already has additionalProperties");
  }
} else {
  console.log("schemas/__defs.schema.json does not appear to be an object schema; no change made.");
}
