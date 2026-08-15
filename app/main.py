from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.config import settings
from app.routers import auth, pairing, profile, chat, ws
from app.services.hp_scheduler import start_scheduler

Base.metadata.create_all(bind=engine)  # dev convenience; use Alembic migrations in production

app = FastAPI(title="Partner App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

app.include_router(auth.router)
app.include_router(pairing.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(ws.router)

_scheduler = None


@app.on_event("startup")
async def on_startup():
    global _scheduler
    _scheduler = start_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
