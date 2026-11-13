import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import psycopg
from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
TOKEN_MINUTES = 60

# A fake hash, so a wrong email takes about as long to reject as a wrong password
DUMMY_HASH = hash_password("not-a-real-password")


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
def login(creds: UserLogin):
    email = creds.email.strip().lower()
    password_bytes = creds.password.encode("utf-8")

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = %s", (email,)
        ).fetchone()

    stored_hash = user["password_hash"] if user else DUMMY_HASH
    password_ok = len(password_bytes) <= 72 and bcrypt.checkpw(
        password_bytes, stored_hash.encode("utf-8")
    )

    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return {"access_token": create_token(user["id"]), "token_type": "bearer"}


@router.post("/signup", status_code=201)
def signup(user: UserCreate):
    # bcrypt only reads the first 72 bytes, so reject longer passwords
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="Password is too long")

    email = user.email.strip().lower()
    password_hash = hash_password(user.password)

    try:
        with get_db() as conn:
            row = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email",
                (email, password_hash),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered")

    return row