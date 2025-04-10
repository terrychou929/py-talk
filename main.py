from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()
active_connections = []

@app.get("/")
async def get():
    with open("chat.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

async def broadcast(message: str):
    for connection in active_connections:
        await connection.send_text(message)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await broadcast("📢 有人加入聊天室")
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                nickname = payload.get("nickname", "Anonymous")
                message = payload.get("message", "")
                full_msg = f"🧑 {nickname}: {message}"
            except json.JSONDecodeError:
                full_msg = f"💬 Unknown message: {data}"

            await broadcast(full_msg)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        await broadcast("❌ 有人離開聊天室")
