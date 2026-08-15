from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth as auth_utils

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=payload.email,
        hashed_password=auth_utils.hash_password(payload.password),
        display_name=payload.display_name or payload.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth_utils.create_access_token(user.id)
    return {"access_token": token}


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not user.hashed_password or not auth_utils.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth_utils.create_access_token(user.id)
    return {"access_token": token}


@router.post("/google", response_model=schemas.Token)
def google_login(payload: schemas.GoogleLogin, db: Session = Depends(get_db)):
    info = auth_utils.verify_google_id_token(payload.id_token)
    google_sub = info["sub"]
    email = info.get("email")

    user = db.query(models.User).filter(models.User.google_sub == google_sub).first()
    if not user:
        # link by email if an account already exists, else create new
        user = db.query(models.User).filter(models.User.email == email).first()
        if user:
            user.google_sub = google_sub
        else:
            user = models.User(
                email=email,
                google_sub=google_sub,
                display_name=info.get("name", email.split("@")[0]),
                avatar_url=info.get("picture"),
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    token = auth_utils.create_access_token(user.id)
    return {"access_token": token}
