import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SERVER_PATH = path.join(__dirname, "mcp/servers/logger/dist/index.js");

console.log("🔌 Connecting to EPOS Logger...");

// Spawn the Logger Server
const server = spawn("node", [SERVER_PATH]);

// Listen for the server's response
server.stdout.on("data", (data) => {
  const response = JSON.parse(data.toString());
  console.log("\n✅ SERVER RESPONSE:", JSON.stringify(response, null, 2));
  
  // Once we get a result, kill the test
  if (response.result) {
    console.log("\n🎉 Test Complete. Check ops/logs/ to see the file!");
    process.kill(server.pid);
    process.exit(0);
  }
});

// Handle Errors
server.stderr.on("data", (data) => console.error(`[Server Error]: ${data}`));

// 1. Send an "Initialize" Request (Handshake)
const initRequest = {
  jsonrpc: "2.0",
  id: 0,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "TerminalTest", version: "1.0" }
  }
};

server.stdin.write(JSON.stringify(initRequest) + "\n");

// 2. Wait 1 second, then send a "Log Event" Request
setTimeout(() => {
  console.log("📨 Sending Log Event...");
  const toolCall = {
    jsonrpc: "2.0",
    id: 1,
    method: "tools/call",
    params: {
      name: "log_event",
      arguments: {
        level: "INFO",
        category: "system.test",
        message: "EPOS Logger is online and functioning.",
        metadata: { test_run: true }
      }
    }
  };
  server.stdin.write(JSON.stringify(toolCall) + "\n");
}, 1000);
