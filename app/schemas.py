import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleLogin(BaseModel):
    id_token: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: Optional[str]
    theme: str
    walkie_talkie_enabled: bool
    hp_tracking_enabled: bool
    hp_decay_hours: int
    is_online: bool
    last_seen: dt.datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = None
    walkie_talkie_enabled: Optional[bool] = None
    hp_tracking_enabled: Optional[bool] = None
    hp_decay_hours: Optional[int] = None


class PairTokenOut(BaseModel):
    token: str
    expires_at: dt.datetime


class PairLinkRequest(BaseModel):
    token: str


class PartnerOut(BaseModel):
    id: str
    display_name: str
    avatar_url: Optional[str]
    is_online: bool
    last_seen: dt.datetime
    hp: int
    walkie_talkie_enabled: bool
    last_message_preview: Optional[str] = None
    last_image_url: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    sender_id: str
    type: str
    text: Optional[str]
    media_url: Optional[str]
    duration_ms: Optional[int]
    created_at: dt.datetime
    delivered_at: Optional[dt.datetime]
    read_at: Optional[dt.datetime]

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    type: str  # "text" | "image" | "voice" | "video_note" | "private_media_meta"
    text: Optional[str] = None
    media_url: Optional[str] = None
    duration_ms: Optional[int] = None
