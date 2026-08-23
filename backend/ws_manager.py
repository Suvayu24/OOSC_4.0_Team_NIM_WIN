from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        stale = []
        for connection in self.active:
            try:
                await connection.send_json(message)
            except Exception:
                stale.append(connection)
        for s in stale:
            self.disconnect(s)


manager = ConnectionManager()
