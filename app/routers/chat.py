import os
import uuid
import datetime as dt
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth as auth_utils, helpers
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

os.makedirs(settings.MEDIA_DIR, exist_ok=True)


@router.get("/messages", response_model=List[schemas.MessageOut])
def get_messages(
    before: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    partnership = helpers.get_partnership(db, current_user.id)
    if not partnership:
        raise HTTPException(status_code=404, detail="Not paired with anyone yet")

    q = db.query(models.Message).filter(models.Message.partnership_id == partnership.id)
    if before:
        before_msg = db.query(models.Message).filter(models.Message.id == before).first()
        if before_msg:
            q = q.filter(models.Message.created_at < before_msg.created_at)
    return q.order_by(models.Message.created_at.desc()).limit(limit).all()


@router.post("/media/upload")
def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """
    Regular media upload (images / voice notes / video notes) — stored on the server.
    NOT used for the private/vault media, which never touches this endpoint — see
    the WebRTC data-channel P2P flow in app/ws/manager.py instead.
    """
    ext = os.path.splitext(file.filename)[1]
    fname = f"{uuid.uuid4()}{ext}"
    path = os.path.join(settings.MEDIA_DIR, fname)
    with open(path, "wb") as f:
        f.write(file.file.read())
    # In production: upload to S3 / GCS and return a signed URL instead of a local path.
    return {"media_url": f"/media/{fname}"}


@router.post("/messages", response_model=schemas.MessageOut)
def create_message(
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """
    REST fallback for sending a message (the app primarily sends messages over the
    WebSocket for realtime delivery — see app/ws — but this endpoint keeps things
    working even if the socket briefly drops).
    """
    partnership = helpers.get_partnership(db, current_user.id)
    if not partnership:
        raise HTTPException(status_code=404, detail="Not paired with anyone yet")

    msg = models.Message(
        partnership_id=partnership.id,
        sender_id=current_user.id,
        type=payload.type,
        text=payload.text,
        media_url=payload.media_url,
        duration_ms=payload.duration_ms,
    )
    db.add(msg)

    if payload.type != models.MessageType.private_media_meta.value:
        helpers.touch_activity(partnership, current_user.id, settings.HP_MAX)

    db.commit()
    db.refresh(msg)
    return msg
