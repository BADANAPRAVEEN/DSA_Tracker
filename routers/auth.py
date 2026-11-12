import bcrypt
import psycopg
from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


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