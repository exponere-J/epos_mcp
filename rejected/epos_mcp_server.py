import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv

# Try importing MCP, fail gracefully if not installed
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ MCP SDK missing. Run: pip install mcp")
    sys.exit(1)

# Setup Paths & Logging
EPOS_ROOT = Path(__file__).parent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("epos_server.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("EPOS")

# --- PHI-3 LOCAL INTELLIGENCE ---
async def query_phi3(prompt: str) -> str:
    """Send a prompt to local Phi-3 via Ollama"""
    try:
        import ollama
        response = ollama.chat(
            model='phi3:mini',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        return f"Phi-3 Error: {str(e)}"

# --- MCP SERVER ---
server = Server("epos-integration")

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="consult_phi3",
            description="Ask the local Phi-3 Mini model for reasoning or routing help.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The question or command"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="system_status",
            description="Check if EPOS files are ready.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    if name == "consult_phi3":
        query = arguments.get("query")
        logger.info(f"🧠 Consulting Phi-3: {query}")
        result = await query_phi3(query)
        return [TextContent(type="text", text=result)]
        
    elif name == "system_status":
        files = list(EPOS_ROOT.glob("*"))
        return [TextContent(type="text", text=f"EPOS Online. Root: {EPOS_ROOT}. Files: {len(files)}")]

    return [TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
