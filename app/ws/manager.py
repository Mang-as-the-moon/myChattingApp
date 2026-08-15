import json
from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    """Holds exactly one active websocket per online user and relays JSON payloads
    to that user's partner. Used for: presence, chat messages, walkie-talkie audio
    chunks, call signaling (offer/answer/ICE), and private-media P2P signaling."""

    def __init__(self):
        self.active: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active

    async def send_to(self, user_id: str, payload: dict):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_text(json.dumps(payload))


manager = ConnectionManager()
