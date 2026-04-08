module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  testMatch: [
    "**/tests/schema/**/*.test.ts",
    "**/tests/runtime/**/*.test.ts",
    "**/tests/telemetry_client/**/*.test.ts"
  ]
};
