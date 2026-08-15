import uuid
import datetime as dt
from sqlalchemy import (
    Column, String, Integer, Boolean, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # null if google-only account
    google_sub = Column(String, unique=True, nullable=True, index=True)

    display_name = Column(String, default="")
    avatar_url = Column(String, nullable=True)

    theme = Column(String, default="system")  # "light" | "dark" | "system"
    walkie_talkie_enabled = Column(Boolean, default=True)
    hp_tracking_enabled = Column(Boolean, default=True)
    hp_decay_hours = Column(Integer, default=6)

    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=dt.datetime.utcnow)

    created_at = Column(DateTime, default=dt.datetime.utcnow)


class PairToken(Base):
    """One-time secret token a user generates and shares out-of-band with their partner."""
    __tablename__ = "pair_tokens"

    id = Column(String, primary_key=True, default=gen_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)


class Partnership(Base):
    """A confirmed 1-to-1 link between exactly two users."""
    __tablename__ = "partnerships"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_a_id = Column(String, ForeignKey("users.id"), nullable=False)
    user_b_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    # responsiveness / "hp" tracking, one value per user in the pair
    hp_a = Column(Integer, default=10)   # A's own responsiveness score (visible to B)
    hp_b = Column(Integer, default=10)   # B's own responsiveness score (visible to A)
    last_activity_a = Column(DateTime, default=dt.datetime.utcnow)  # last time A sent something
    last_activity_b = Column(DateTime, default=dt.datetime.utcnow)  # last time B sent something
    last_hp_tick_a = Column(DateTime, default=dt.datetime.utcnow)
    last_hp_tick_b = Column(DateTime, default=dt.datetime.utcnow)


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    voice = "voice"
    video_note = "video_note"
    private_media_meta = "private_media_meta"  # metadata only, no server-stored file


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    partnership_id = Column(String, ForeignKey("partnerships.id"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)

    type = Column(Enum(MessageType), default=MessageType.text)
    text = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)  # only set for image/voice/video_note (server storage)
    duration_ms = Column(Integer, nullable=True)  # for voice/video notes

    created_at = Column(DateTime, default=dt.datetime.utcnow, index=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
