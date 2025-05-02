from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import json
import os

from models import Base, Room, User, Message

# FastAPI 應用
app = FastAPI()

# 資料庫配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/chatdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 創建表格
Base.metadata.create_all(bind=engine)

# 儲存 WebSocket 連線
room_connections = {}  # {room_id: set(websocket)}

# 提供前端 HTML
@app.get("/")
async def get():
    with open("chat.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 廣播訊息
async def broadcast(room_id: int, message: str, db: Session):
    if room_id not in room_connections:
        return
    for conn in room_connections[room_id].copy():
        try:
            await conn.send_text(message)
        except WebSocketDisconnect:
            room_connections[room_id].remove(conn)
            # 查找斷線用戶
            user = db.query(User).filter(User.id == conn.user_id).first()
            if user:
                await broadcast(room_id, f"❌ {user.nickname} left room", db)
                db.delete(user)
                db.commit()
            if not room_connections[room_id]:
                del room_connections[room_id]

# WebSocket 端點
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()

    try:
        # 接收初始資料
        init_data = await websocket.receive_text()
        init = json.loads(init_data)
        room_name = init.get("room")
        password = init.get("password")
        nickname = init.get("nickname", "Anonymous")

        # 驗證輸入
        if not room_name or len(room_name) > 50 or not isinstance(room_name, str):
            await websocket.send_text("❌ Invalid room name.")
            await websocket.close()
            return
        
        if not password or len(password) > 50 or not isinstance(password, str):
            await websocket.send_text("❌ Invalid password.")
            await websocket.close()
            return

        # 檢查或創建房間
        room = db.query(Room).filter(Room.name == room_name).first()
        if not room:
            room = Room(name=room_name, password=password)
            db.add(room)
            db.commit()
            db.refresh(room)
        elif room.password != password:
            await websocket.send_text("❌ Wrong password.")
            await websocket.close()
            return

        # 創建用戶
        user = User(nickname=nickname, room_id=room.id)
        db.add(user)
        db.commit()
        db.refresh(user)

        # 初始化房間連線
        if room.id not in room_connections:
            room_connections[room.id] = set()
        room_connections[room.id].add(websocket)
        websocket.user_id = user.id  # 儲存用戶 ID 以便斷線時查找

        # 廣播加入訊息
        await broadcast(room.id, f"🔔 {nickname} joined room '{room_name}'", db)

        # 主循環：處理訊息
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                message = payload.get("message")
                if not isinstance(message, str) or not message:
                    continue
                msg = Message(room_id=room.id, user_id=user.id, message=message)
                db.add(msg)
                db.commit()
                broadcast_msg = f"🧑 {nickname}: {message}"
            except json.JSONDecodeError:
                broadcast_msg = f"💬 {nickname}: {data}"
            await broadcast(room.id, broadcast_msg, db)

    except WebSocketDisconnect:
        if room.id in room_connections and websocket in room_connections[room.id]:
            room_connections[room.id].remove(websocket)
            await broadcast(room.id, f"❌ {nickname} left room '{room_name}'", db)
            # 刪除用戶
            db.delete(user)
            db.commit()
            if not room_connections[room.id]:
                del room_connections[room.id]
    finally:
        db.close()
        await websocket.close()