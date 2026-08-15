import datetime as dt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app import models
from app.ws.manager import manager


async def decay_hp_job():
    """Runs periodically. For each partnership + direction, if the sender hasn't sent
    anything since their last hp tick and enough decay-hours have passed, drop hp by 1
    (down to 0) and notify the partner over the socket if they're online."""
    db = SessionLocal()
    try:
        now = dt.datetime.utcnow()
        partnerships = db.query(models.Partnership).all()
        for p in partnerships:
            user_a = db.query(models.User).filter(models.User.id == p.user_a_id).first()
            user_b = db.query(models.User).filter(models.User.id == p.user_b_id).first()

            for user, is_a in ((user_a, True), (user_b, False)):
                if not user or not user.hp_tracking_enabled:
                    continue
                last_tick = p.last_hp_tick_a if is_a else p.last_hp_tick_b
                hp = p.hp_a if is_a else p.hp_b
                decay_hours = user.hp_decay_hours or 6

                if hp <= 0:
                    continue
                if now - last_tick >= dt.timedelta(hours=decay_hours):
                    new_hp = max(0, hp - 1)
                    if is_a:
                        p.hp_a = new_hp
                        p.last_hp_tick_a = now
                    else:
                        p.hp_b = new_hp
                        p.last_hp_tick_b = now
                    db.commit()

                    partner_id = p.user_b_id if is_a else p.user_a_id
                    await manager.send_to(partner_id, {
                        "type": "hp_update", "for_user_id": user.id, "hp": new_hp,
                    })
    finally:
        db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(decay_hp_job, "interval", minutes=15)
    scheduler.start()
    return scheduler
