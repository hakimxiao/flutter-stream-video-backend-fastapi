from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import jwt

from datetime import datetime, timedelta, timezone

from database.connection import get_db
from models.user import User
from schemas.auth import SignupRequest, UserResponse, LoginRequest
from core.config import settings


router = APIRouter()
password_hash = PasswordHash.recommended()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    # 1. Cek email
    existing_user = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # 2. Hash password
    hashed_password = password_hash.hash(payload.password)

    # 3. Buat objek pengguna
    user = User(
        email=str(payload.email),
        hashed_password=hashed_password
    )

    # 4. Simpan pengguna ke database
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.roleback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # 5. return data publik
    return user

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # 1. Cari email
    user = db.scalar(select(User).where(User.email == payload.email))

    # 2. Pesan sama untuk email dan password yang salah
    if user is None or not password_hash.verify(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 3. Waktu kedaluarsa token
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    # 4. Buat payload jwt
    token_payload = {
        "sub": str(user.id),
        "exp": expires_at
    }

    # 5. Sahkan token
    access_token = jwt.encode(
        token_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }