import datetime as dt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models, auth as auth_utils, helpers
from app.config import settings
from app.ws.manager import manager

router = APIRouter(tags=["ws"])

# Message "type" values relayed over this socket:
#   presence          -> broadcast automatically on connect/disconnect
#   chat_message       {type, text?, media_url?, duration_ms?}
#   typing              {}
#   walkie_start / walkie_chunk(base64 audio) / walkie_end   -- push-to-talk
#   call_offer / call_answer / ice_candidate / call_end       -- WebRTC signaling for audio/video calls
#   private_offer / private_answer / private_ice / private_end -- WebRTC signaling for the local-only
#                                                                  encrypted media vault (data channel only,
#                                                                  file bytes never pass through this server)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    user_id = auth_utils.decode_access_token(token)
    if not user_id:
        await websocket.close(code=4401)
        return

    db: Session = SessionLocal()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        await websocket.close(code=4401)
        db.close()
        return

    partnership = helpers.get_partnership(db, user_id)
    partner_id = None
    if partnership:
        partner_id = partnership.user_b_id if partnership.user_a_id == user_id else partnership.user_a_id

    await manager.connect(user_id, websocket)
    user.is_online = True
    db.commit()

    if partner_id:
        await manager.send_to(partner_id, {"type": "presence", "user_id": user_id, "is_online": True})

    try:
        while True:
            payload = await websocket.receive_json()
            msg_type = payload.get("type")

            if not partner_id:
                continue  # no partner linked yet, nothing to relay

            if msg_type == "chat_message":
                msg = models.Message(
                    partnership_id=partnership.id,
                    sender_id=user_id,
                    type=payload.get("message_type", "text"),
                    text=payload.get("text"),
                    media_url=payload.get("media_url"),
                    duration_ms=payload.get("duration_ms"),
                )
                db.add(msg)
                if msg.type != models.MessageType.private_media_meta:
                    helpers.touch_activity(partnership, user_id, settings.HP_MAX)
                db.commit()
                db.refresh(msg)
                await manager.send_to(partner_id, {
                    "type": "chat_message",
                    "id": msg.id,
                    "sender_id": user_id,
                    "message_type": msg.type.value,
                    "text": msg.text,
                    "media_url": msg.media_url,
                    "duration_ms": msg.duration_ms,
                    "created_at": msg.created_at.isoformat(),
                })
                # let sender's client know the partner's hp reset too if applicable
                continue

            # Everything else (walkie_*, call_*, private_*, typing) is a pure relay —
            # the server never inspects or stores this content, it just forwards it
            # to the partner's open socket so peers can negotiate WebRTC directly.
            payload["from"] = user_id
            await manager.send_to(partner_id, payload)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id)
        user.is_online = False
        user.last_seen = dt.datetime.utcnow()
        db.commit()
        if partner_id:
            await manager.send_to(partner_id, {
                "type": "presence", "user_id": user_id, "is_online": False,
                "last_seen": user.last_seen.isoformat(),
            })
        db.close()
