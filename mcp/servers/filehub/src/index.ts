import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";
import { z } from "zod";

// Define the server
const server = new Server(
  {
    name: "epos-filehub",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Security: Restrict operations to the EPOS root
// We assume this server runs inside mcp/servers/filehub, so we go up 3 levels
const EPOS_ROOT = path.resolve(__dirname, "../../../");

// Helper: Validate path security
function getSecurePath(relativePath: string): string {
  const resolved = path.resolve(EPOS_ROOT, relativePath);
  if (!resolved.startsWith(EPOS_ROOT)) {
    throw new Error(`Access denied: Path must be within EPOS root: ${resolved}`);
  }
  return resolved;
}

// 1. List Tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "list_directory",
        description: "List files and folders in a directory within EPOS.",
        inputSchema: zodToJsonSchema(
          z.object({
            path: z.string().describe("Relative path to list (e.g. 'sites/pgp')"),
          })
        ),
      },
      {
        name: "read_file",
        description: "Read the contents of a file (UTF-8).",
        inputSchema: zodToJsonSchema(
          z.object({
            path: z.string().describe("Relative path to the file"),
          })
        ),
      },
      {
        name: "write_file",
        description: "Write content to a file (overwrites if exists).",
        inputSchema: zodToJsonSchema(
          z.object({
            path: z.string().describe("Relative path to the file"),
            content: z.string().describe("The content to write"),
          })
        ),
      },
    ],
  };
});

// 2. Handle Tool Calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "list_directory") {
      const dirPath = getSecurePath(String(args?.path || "."));
      const files = await fs.readdir(dirPath, { withFileTypes: true });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              files.map((f) => ({
                name: f.name,
                type: f.isDirectory() ? "directory" : "file",
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "read_file") {
      const filePath = getSecurePath(String(args?.path));
      const content = await fs.readFile(filePath, "utf-8");
      return {
        content: [{ type: "text", text: content }],
      };
    }

    if (name === "write_file") {
      const filePath = getSecurePath(String(args?.path));
      const content = String(args?.content);
      
      // Ensure directory exists
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, content, "utf-8");
      
      return {
        content: [{ type: "text", text: `Successfully wrote to ${args?.path}` }],
      };
    }

    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
  } catch (error: any) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

// Helper to convert Zod to JSON Schema
function zodToJsonSchema(schema: any) {
  // Simple shim for the example; normally we'd use zod-to-json-schema package
  // but for this basic setup, we return a structure fitting MCP needs.
  // This is a simplified representation.
  return {
    type: "object",
    properties: {
      path: { type: "string" },
      content: { type: "string" }
    },
    required: ["path"]
  };
}

// Start the server
async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Logging to stderr so it doesn't interfere with JSON communication on stdout
  console.error("EPOS FileHub running on stdio");
}

run().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
