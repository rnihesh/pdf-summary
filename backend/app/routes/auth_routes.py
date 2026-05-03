from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from ..db import get_db
from ..models import User
from ..schemas import SignupIn, LoginIn, GoogleIn, TokenOut
from ..auth import hash_password, verify_password, create_access_token
from ..config import settings

router = APIRouter()


@router.post("/signup", response_model=TokenOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user_email=user.email)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenOut(access_token=create_access_token(user.id), user_email=user.email)


@router.post("/google", response_model=TokenOut)
def google_signin(payload: GoogleIn, db: Session = Depends(get_db)):
    audiences = settings.google_audiences
    if not audiences:
        raise HTTPException(status_code=503, detail="Google sign-in not configured")
    info = None
    last_err = None
    for aud in audiences:
        try:
            info = google_id_token.verify_oauth2_token(
                payload.id_token, google_requests.Request(), aud
            )
            break
        except ValueError as e:
            last_err = e
            continue
    if info is None:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {last_err}")
    if not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email not verified")
    email = info["email"]
    sub = info["sub"]
    user = db.execute(select(User).where(User.google_sub == sub)).scalar_one_or_none()
    if not user:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user:
            user.google_sub = sub
        else:
            user = User(email=email, google_sub=sub)
            db.add(user)
        db.commit()
        db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user_email=user.email)
