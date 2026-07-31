from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from common.config import settings
from common.database import Base, SessionLocal, engine, get_db
from common.models import User
from common.observability import instrument_fastapi
from common.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from common.security import (
    create_access_token,
    find_user_by_email,
    get_current_user,
    hash_password,
    verify_password,
)

SERVICE = "noli-auth-service"


def seed_admin() -> None:
    db = SessionLocal()
    try:
        email = settings.admin_email.lower()
        if find_user_by_email(db, email):
            return
        db.add(
            User(
                email=email,
                password_hash=hash_password(settings.admin_password),
                full_name="NOLI Admin",
                phone="0900000000",
                is_admin=True,
            )
        )
        db.commit()
        print(f"[{SERVICE}] seeded admin {email}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        seed_admin()
    yield


app = FastAPI(title=SERVICE, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
instrument_fastapi(app, SERVICE)


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE}


@app.post("/api/auth/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if find_user_by_email(db, email):
        raise HTTPException(409, "Email đã được đăng ký")
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip(),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=create_access_token(user.id, user.is_admin),
        user=UserOut.model_validate(user),
    )


@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = find_user_by_email(db, payload.email.lower().strip())
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    return TokenOut(
        access_token=create_access_token(user.id, user.is_admin),
        user=UserOut.model_validate(user),
    )


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
