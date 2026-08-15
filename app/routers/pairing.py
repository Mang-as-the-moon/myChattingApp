import secrets
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth as auth_utils

router = APIRouter(prefix="/pairing", tags=["pairing"])


def _get_partnership(db: Session, user_id: str):
    return db.query(models.Partnership).filter(
        (models.Partnership.user_a_id == user_id) | (models.Partnership.user_b_id == user_id)
    ).first()


@router.post("/generate-token", response_model=schemas.PairTokenOut)
def generate_token(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    if _get_partnership(db, current_user.id):
        raise HTTPException(status_code=400, detail="You are already paired with a partner")

    # invalidate previous unused tokens
    db.query(models.PairToken).filter(
        models.PairToken.owner_id == current_user.id, models.PairToken.used == False  # noqa: E712
    ).delete()

    token_value = secrets.token_urlsafe(9)  # short, shareable secret
    pt = models.PairToken(
        owner_id=current_user.id,
        token=token_value,
        expires_at=dt.datetime.utcnow() + dt.timedelta(hours=24),
    )
    db.add(pt)
    db.commit()
    return {"token": token_value, "expires_at": pt.expires_at}


@router.post("/link")
def link_partner(
    payload: schemas.PairLinkRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    if _get_partnership(db, current_user.id):
        raise HTTPException(status_code=400, detail="You are already paired with a partner")

    pt = db.query(models.PairToken).filter(
        models.PairToken.token == payload.token, models.PairToken.used == False  # noqa: E712
    ).first()
    if not pt or pt.expires_at < dt.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if pt.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot pair with yourself")

    pt.used = True
    partnership = models.Partnership(user_a_id=pt.owner_id, user_b_id=current_user.id)
    db.add(partnership)
    db.commit()
    db.refresh(partnership)
    return {"partnership_id": partnership.id}


@router.delete("/unlink")
def unlink(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    p = _get_partnership(db, current_user.id)
    if not p:
        raise HTTPException(status_code=404, detail="No partnership found")
    db.delete(p)
    db.commit()
    return {"status": "unlinked"}
