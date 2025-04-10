from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# { "room_name": {"password": "1234", "connections": set([...])} }
rooms = {}

@app.get("/")
async def get():
    with open("chat.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Broadcast specific room
async def broadcast(room: str, message: str):
    if room not in rooms:
        return
    for conn in rooms[room]["connections"].copy():
        try:
            await conn.send_text(message)
        except WebSocketDisconnect:
            rooms[room]["connections"].remove(conn)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Collect data：room, password, nickname
    init_data = await websocket.receive_text()
    try:
        init = json.loads(init_data)
        room = init.get("room")
        password = init.get("password")
        nickname = init.get("nickname", "Anonymous")
    except Exception:
        await websocket.send_text("❌ Invalid join info.")
        await websocket.close()
        return

    if room not in rooms:
        rooms[room] = {"password": password, "connections": set()}
    elif rooms[room]["password"] != password:
        await websocket.send_text("❌ Wrong password.")
        await websocket.close()
        return

    # ✅ Join Room
    rooms[room]["connections"].add(websocket)
    await broadcast(room, f"🔔 {nickname} joined room '{room}'")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                msg = f"🧑 {nickname}: {payload.get('message')}"
            except json.JSONDecodeError:
                msg = f"💬 {nickname}: {data}"

            await broadcast(room, msg)

    except WebSocketDisconnect:
        rooms[room]["connections"].remove(websocket)
        await broadcast(room, f"❌ {nickname} left room '{room}'")
