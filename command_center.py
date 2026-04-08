# File: command_center.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from pathlib import Path
from event_bus import get_event_bus

app = FastAPI(title="EPOS Command Center")
bus = get_event_bus()

# Serve UI files
app.mount("/static", StaticFiles(directory="static"), name="static")

class CanvasManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = CanvasManager()

@app.on_event("startup")
async def start_monitoring():
    async def listen_to_bus():
        # This bridges the internal EPOS Nervous System to your Browser
        def handle_event(event):
            asyncio.create_task(manager.broadcast(event))
        
        bus.subscribe("*", handle_event)
        bus.start_polling()

    asyncio.create_task(listen_to_bus())

@app.websocket("/ws/canvas")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle commands from the UI (e.g. "Trigger Diagnostic")
            print(f"UI Command Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)