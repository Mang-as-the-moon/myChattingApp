from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth as auth_utils, helpers
from app.config import settings

router = APIRouter(tags=["profile"])


@router.get("/profile/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth_utils.get_current_user)):
    return current_user


@router.put("/profile/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/profile/partner", response_model=schemas.PartnerOut)
def get_partner(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    partnership = helpers.get_partnership(db, current_user.id)
    if not partnership:
        raise HTTPException(status_code=404, detail="Not paired with anyone yet")

    partner = helpers.get_partner_user(db, partnership, current_user.id)
    hp = helpers.hp_for_user(partnership, partner.id)

    last_msg = db.query(models.Message).filter(
        models.Message.partnership_id == partnership.id
    ).order_by(models.Message.created_at.desc()).first()

    last_image = db.query(models.Message).filter(
        models.Message.partnership_id == partnership.id,
        models.Message.type == models.MessageType.image,
    ).order_by(models.Message.created_at.desc()).first()

    return schemas.PartnerOut(
        id=partner.id,
        display_name=partner.display_name,
        avatar_url=partner.avatar_url,
        is_online=partner.is_online,
        last_seen=partner.last_seen,
        hp=hp,
        walkie_talkie_enabled=partner.walkie_talkie_enabled and current_user.walkie_talkie_enabled,
        last_message_preview=(last_msg.text if last_msg and last_msg.type == models.MessageType.text else (f"[{last_msg.type.value}]" if last_msg else None)),
        last_image_url=last_image.media_url if last_image else None,
    )
