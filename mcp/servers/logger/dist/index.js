import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, ErrorCode, McpError, } from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";
import { z } from "zod";
import { v4 as uuidv4 } from "uuid";
import { fileURLToPath } from "url";
// Fix for __dirname in ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Configuration
const LOG_DIR = path.resolve(__dirname, "../../../ops/logs");
const SESSION_ID = uuidv4();
const server = new Server({
    name: "epos-logger",
    version: "1.0.0",
}, {
    capabilities: {
        tools: {},
    },
});
// Schema for a Log Entry
const LogSchema = z.object({
    level: z.enum(["INFO", "WARN", "ERROR", "DEBUG", "CRITICAL"]),
    category: z.string().describe("The domain (e.g., 'content', 'system', 'agent')"),
    message: z.string(),
    // THE FIX: Explicitly define Key and Value types for the record
    metadata: z.record(z.string(), z.any()).optional().describe("Structured data for the MARL engine"),
});
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "log_event",
                description: "Log a structured event. Critical for tracking agent process adherence.",
                inputSchema: {
                    type: "object",
                    properties: {
                        level: { type: "string", enum: ["INFO", "WARN", "ERROR", "DEBUG", "CRITICAL"] },
                        category: { type: "string" },
                        message: { type: "string" },
                        metadata: { type: "object" }
                    },
                    required: ["level", "category", "message"]
                },
            },
        ],
    };
});
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    if (name === "log_event") {
        const parsed = LogSchema.safeParse(args);
        if (!parsed.success) {
            throw new McpError(ErrorCode.InvalidParams, "Invalid log format");
        }
        const entry = {
            timestamp: new Date().toISOString(),
            session_id: SESSION_ID,
            ...parsed.data,
        };
        const dateStr = new Date().toISOString().split("T")[0];
        const logFile = path.join(LOG_DIR, `epos_${dateStr}.jsonl`);
        await fs.mkdir(LOG_DIR, { recursive: true });
        await fs.appendFile(logFile, JSON.stringify(entry) + "\n", "utf-8");
        return {
            content: [{ type: "text", text: `Logged: [${entry.level}] ${entry.message}` }],
        };
    }
    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
});
async function run() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
}
run().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});
