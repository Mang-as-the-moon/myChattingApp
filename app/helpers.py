from sqlalchemy.orm import Session
from app import models


def get_partnership(db: Session, user_id: str):
    return db.query(models.Partnership).filter(
        (models.Partnership.user_a_id == user_id) | (models.Partnership.user_b_id == user_id)
    ).first()


def get_partner_user(db: Session, partnership: models.Partnership, current_user_id: str):
    partner_id = partnership.user_b_id if partnership.user_a_id == current_user_id else partnership.user_a_id
    return db.query(models.User).filter(models.User.id == partner_id).first()


def hp_for_user(partnership: models.Partnership, user_id: str) -> int:
    """Returns the HP value that represents `user_id`'s own responsiveness (shown to their partner)."""
    return partnership.hp_a if partnership.user_a_id == user_id else partnership.hp_b


def touch_activity(partnership: models.Partnership, sender_id: str, hp_max: int):
    """Call whenever `sender_id` sends a message/image/voice — resets their own hp and activity timestamp."""
    import datetime as dt
    now = dt.datetime.utcnow()
    if partnership.user_a_id == sender_id:
        partnership.last_activity_a = now
        partnership.last_hp_tick_a = now
        partnership.hp_a = hp_max
    else:
        partnership.last_activity_b = now
        partnership.last_hp_tick_b = now
        partnership.hp_b = hp_max
